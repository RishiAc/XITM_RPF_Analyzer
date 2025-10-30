# src/api/app.py
import os
import uuid
from typing import List, Dict, Optional, Union
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from sentence_transformers import SentenceTransformer, CrossEncoder
from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse
from supabase import create_client, Client

# src/api/app.py (only showing the diffs/additions)

# ---- env ----
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "rfp_chunks")
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
# ---- singletons ----
_app_model = SentenceTransformer(EMBED_MODEL)
_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=20)
_sb: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def _ensure_collection(dim: int):
    try:
        _client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE),
        )
    except UnexpectedResponse as e:
        code = getattr(e, "status_code", None)
        if code in (409, 403):
            pass  # already exists or not allowed to create; assume it exists
        else:
            raise
    # ensure payload indexes every time (idempotent below)
    _ensure_payload_index()

def _ensure_payload_index():
    """
    Create an index on payload key 'doc_id' so we can filter by it.
    Qdrant expects KEYWORD (exact-match) for MatchValue filters.
    """
    try:
        _client.create_payload_index(
            collection_name=QDRANT_COLLECTION,
            field_name="doc_id",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )
    except UnexpectedResponse as e:
        code = getattr(e, "status_code", None)
        # 409: already indexed; 403: not allowed (ok if already exists)
        if code in (409, 403):
            return
        raise

def _embed(chunks: List[Dict[str, Union[int, str]]]) -> List[List[float]]:
    texts = [chunk["text"] for chunk in chunks]

    vecs = _app_model.encode(texts, normalize_embeddings=True)
    return [v.tolist() for v in vecs]

def _fetch_query_table(query_numbers: Optional[List[int]] = None) -> List[Dict]:
    """
    SELECT query_number, knowledge_base_answer, rfp_query_text, weight
    FROM public.Query_Table
    [WHERE query_number IN (...)]
    ORDER BY query_number ASC
    """
    q = _sb.table("Query_Table").select(
        "query_number, knowledge_base_answer, rfp_query_text, weight"
    ).order("query_number", desc=False)

    if query_numbers:
        q = q.in_("query_number", query_numbers)

    res = q.execute()
    return res.data or []

router = APIRouter(prefix = "/vector", tags=["vector"])

class IngestBody(BaseModel):
    doc_id: str
    chunks: List[Dict[str, Union[int, str]]]

class SearchBody(BaseModel):
    doc_id: str
    query: str
    top_k: Optional[int] = 5

class OrchestrateBody(BaseModel):
    rfp_id: str            # maps to RFPs.id
    rfp_doc_id: str        # Qdrant payload doc_id for this RFP
    top_k: Optional[int] = 5
    query_numbers: Optional[List[int]] = None  # optional subset


@router.get("/health")
def health():
    return {"ok": True}

@router.post("/ingest-chunks")
def ingest_chunks(body: IngestBody):
    try:
        if not body.chunks:
            raise HTTPException(400, "chunks cannot be empty")

        vecs = _embed(body.chunks)
        dim = len(vecs[0])
        _ensure_collection(dim)

        # Use UUIDs for Qdrant point IDs (required: int or UUID)
        points = []
        for i, c in enumerate(body.chunks):
            pid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{body.doc_id}:{i}"))  # deterministic UUID
            vector = vecs[i]
            points.append(
                models.PointStruct(
                    id=pid,
                    vector=vector,
                    payload={"doc_id": body.doc_id, "text": c["text"], "page_num": c["chunk_num"]}
                )
            )

        # Batch upsert
        for i in range(0, len(points), 256):
            _client.upsert(collection_name=QDRANT_COLLECTION, points=points[i:i+256])

        return {"ok": True, "doc_id": body.doc_id, "ingested": len(points)}

    except HTTPException:
        raise
    except UnexpectedResponse as e:
        # Surface Qdrant status info to the client for easier debugging
        code = getattr(e, "status_code", None)
        raise HTTPException(status_code=502, detail=f"Qdrant upsert error: {code} {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ingest-chunks error: {type(e).__name__}: {e}")

@router.post("/search")
def search(body: SearchBody):
    try:
        qvec = _embed([{"text": body.query}])[0]
        filt = models.Filter(
            must=[models.FieldCondition(key="doc_id", match=models.MatchValue(value=body.doc_id))]
        )
        hits = _client.search(
            collection_name=QDRANT_COLLECTION,
            query_vector=qvec,
            limit=body.top_k,
            query_filter=filt,
            with_payload=True,
            with_vectors=True
        )
        return rerank(hits, body.query)
        
    except UnexpectedResponse as e:
        code = getattr(e, "status_code", None)
        raise HTTPException(status_code=502, detail=f"Qdrant search error: {code} {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"search error: {type(e).__name__}: {e}")

@router.post("/orchestrate-queries")
def orchestrate_queries(body: OrchestrateBody):
    """
    Loops through Query_Table, calls EXISTING /vector/search for each query,
    and returns a bare JSON payload for the LLM layer.
    """
    try:
        # 1) Load query set
        rows = _fetch_query_table(body.query_numbers)
        if not rows:
            raise HTTPException(status_code=400, detail="No queries found in Query_Table")

        results = []

        # 2) For each query, call your existing search() with SearchBody
        for row in rows:
            qnum = row.get("query_number")
            rfp_q = (row.get("rfp_query_text") or "").strip()
            kb_ans = (row.get("knowledge_base_answer") or "").strip()
            weight = row.get("weight")

            kb_embedding = []

            if kb_ans:
                kb_embedding = _embed([{"text": kb_ans}])[0]

            if not rfp_q:
                # Still include the record with empty citations; LLM layer can decide to skip
                rfp_topk = []
            else:
                # IMPORTANT: Call your existing search() function directly
                sb = SearchBody(doc_id=body.rfp_doc_id, query=rfp_q, top_k=body.top_k or 5)
                search_resp = search(sb)  # <-- reuses your /vector/search implementation

                print("-"*50)
                print(search_resp)

                # previous code would cause attribute error since search_resp returns a list of (hit, score)
                rfp_topk = [resp[0] for resp in search_resp]

            # Shape for LLM layer
            results.append({
                "rfp_id": body.rfp_id,
                "query_number": qnum,
                "rfp_query_text": rfp_q,
                "knowledge_base_answer": kb_ans,
                "knowledge_base_answer_embedding": kb_embedding,
                "weight": weight,
                "rfp_topk": rfp_topk,
            })

        return {
            "rfp_id": body.rfp_id,
            "total_queries": len(results),
            "queries": results
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"orchestrate-queries error: {type(e).__name__}: {e}")
def rerank(hits, query):
    reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    texts = [hit.payload["text"] for hit in hits]
    scores = reranker.predict([(query, text) for text in texts])
    reranked_results = [
        (hits[i], float(scores[i]))
        for i in range(len(hits))
    ]
    reranked_results.sort(key=lambda x: x[1], reverse=True)
    return reranked_results