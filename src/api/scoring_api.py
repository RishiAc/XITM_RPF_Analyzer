from fastapi import APIRouter
from api.vector_api import OrchestrateBody, orchestrate_queries
from pydantic import BaseModel
import numpy as np
from api.clients.supabase import _sb

router = APIRouter(prefix="/score", tags=["score"])

class QueryPair(BaseModel):
    kb_answer: str
    rfp_query_text: str
    rfp_query_embedding: list[float]

# because we are using the same model across services (upserting into db and embedding chunks and questions)
# I am assuming the dimensions are the same in this method\

# TODO: Have a more strict check of dimensions and vectors across code
def _cosine_similarity(v1, v2):
    a = np.array(v1, dtype=float)
    b = np.array(v2, dtype=float)

    cos_sim = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    return cos_sim

def _upsert_rfp_eval(rfp_id, chunks, query_number, question, ans, score):

    print(f"Attemtping Upsert: {rfp_id} {query_number} {question} {ans} {score}")

    try:
        data, count = _sb.table("RFP_Evals").upsert({
            "rfp_id": rfp_id,
            "query_number": query_number,
            "question": question,
            "knowledge_base_chunk": ans,
            "rfp_citation_chunks": chunks,
            "score": score
        }).execute()

        print(data)
        print(count)
    except Exception as e:
        print(f"Upsert Failed With Unknown Exception:\n {e}")

def _calculate_score(chunks, ans_embedding):

    total_cos_sim = 0

    # assuming chunks are qdrant stored point objects
    for chunk in chunks:
        print("-"*50)
        print(chunk)

        chunk_embedding = chunk.vector
        chunk_text = chunk.payload["text"]
        chunk_page_num = chunk.payload["page_num"]

        # compute the similarity score
        cos_sim = _cosine_similarity(list(chunk_embedding), list(ans_embedding))
        total_cos_sim += cos_sim
    
    return total_cos_sim

@router.post("/score-rfp")
def score_rfp(body: OrchestrateBody):

    tests = orchestrate_queries(body)

    score = 0

    for test in tests["queries"]:
        query_number = test["query_number"]
        question = test["rfp_query_text"]
        ans = test["knowledge_base_answer"]
        ans_embedding = test["knowledge_base_answer_embedding"]
        weight = test["weight"]

        rfp_chunks = test["rfp_topk"]

        total_cos_sim = _calculate_score(rfp_chunks, ans_embedding)
        _upsert_rfp_eval(body.rfp_id, rfp_chunks, query_number, question, ans, total_cos_sim)

        score += total_cos_sim * weight
        
    return {
        "score": max(0, score)
    }