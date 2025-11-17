from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from api.vector_api import search, SearchBody
from pprint import pprint
from qdrant_client.models import ScoredPoint
from api.clients.openai import get_chat_completion

router = APIRouter(prefix="/query", tags=["query"])

class QueryBody(BaseModel):
    query: str
    rfp_doc_id: str # id in qdrant

class ChunkResponse(BaseModel):
    chunk_text: str
    confidence: float

class SummaryResponse(BaseModel):
    answer: str
    sources: list[str]

def _gen_rfp_summary_sys_prompt(chunks: list[ChunkResponse]) -> str:

    chunk_texts = []

    print('CHUNK CONTEXT')

    for chunk in chunks:
        print("-"*50)
        print(chunk.chunk_text)

        chunk_texts.append(chunk.chunk_text)

    print(f"Finished processing chunks {len(chunk_texts)}")
    print(type(chunk_texts[0]))

    chunk_content = "\n\n".join(chunk_texts)

    print(f"LEN OF CHUNK CONTEXT: {len(chunk_content)}")

    system_prompt = f"""
    
    ### Role: 
    
    You are a business development analyst for a IT government contracting firm. Your job is to answer a representatives query thouroughly 
    and accuratey.

    ### Task:

    You will be given the following pieces of information:
    1. A list of relevant chunks of text from a request for proposal document
    2. A query that a representative has

    Your role is to extract and provide the following information:
    1. An answer to the representative's query based solely on the chunks of text that you are given
    2. A list of sources that are relevant to your answer. A source is a sentence present in one of the chunks of text from the request for 
    proposal document

    ### Ground Rules:
    1. You MUST answer the query based on the chunks of text from the request for proposal document
    2. Each source you provide must not be longer than a sentence. If you use multiply sentence those are seperate sources.
    3. Assume that the person reading your response does not have the document with them. For your sources you must provide the full quote you used.
    4. You answer should be as specific and verbose as possible.
    5. They should be easy to read for a business development analyst.
    6. Don't include your sources in the answer field. Only include them in the sources field.

    ### Chunks from request for proposal

    {chunk_content}

    """

    return system_prompt

def _generate_summary(query: str, chunks: list[ChunkResponse]) -> SummaryResponse:
    system_prompt = _gen_rfp_summary_sys_prompt(chunks=chunks)

    print("SYSTEM PROMPT:")
    print(system_prompt)

    response : SummaryResponse = get_chat_completion(
        system_message=system_prompt,
        user_prompt=query,
        response_format=SummaryResponse
    )

    print("Answer:")
    print(response.answer)

    print("\nSources:")
    print(response.sources)

    return response
def _process_chunks(res) -> list[ChunkResponse]:
    """
    Convert search() results into ChunkResponse list.

    Handles:
    - list of dicts from rerank(): [{"text","score",...}, ...]
    - dict with "results": {"results": [...]} (future-proof)
    """
    chunks: list[ChunkResponse] = []

    # If the search result is a dict with "results", unwrap it
    if isinstance(res, dict):
        items = res.get("results", [])
    else:
        items = res

    for item in items:
        # item is expected to be a dict like: {"text","score",...}
        text = item.get("text", "") if isinstance(item, dict) else ""
        score = float(item.get("score", 0.0)) if isinstance(item, dict) else 0.0

        new_chunk = ChunkResponse(
            chunk_text=text,
            confidence=score
        )
        chunks.append(new_chunk)

    return chunks

@router.post("/query-rfp")
def query_rfp(body: QueryBody):

    try:
        print(body.query)
        print(body.rfp_doc_id)

        payload = SearchBody(
            doc_id = body.rfp_doc_id,
            query = body.query,
            top_k = 20
        )

        res = search(payload)
        print("RAW SEARCH RESPONSE:", res)
        chunks = _process_chunks(res)
        # Defensive: if no chunks returned, return 400 with helpful message
        if not chunks:
            raise HTTPException(status_code=400, detail=f"No chunks found for doc_id={body.rfp_doc_id}. Verify the doc_id and that chunks were ingested.")
        response : SummaryResponse = _generate_summary(body.query, chunks)

        return response
    
    except Exception as e:
        print("Error in query_rfp:", type(e).__name__, e)
        raise HTTPException(status_code=400, detail=str(e))