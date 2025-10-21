# src/api/app.py
import os
import uuid
from typing import List, Dict, Optional, Union
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from sentence_transformers import SentenceTransformer, CrossEncoder
from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse

# src/api/app.py (only showing the diffs/additions)

# ---- env ----
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "rfp_chunks")
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# ---- singletons ----
_app_model = SentenceTransformer(EMBED_MODEL)
_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=20)

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

router = APIRouter(prefix="/vector", tags=["vector"])

class IngestBody(BaseModel):
    doc_id: str
    chunks: List[Dict[str, Union[int, str]]]

class SearchBody(BaseModel):
    doc_id: str
    query: str
    top_k: Optional[int] = 5

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
        )
        return rerank(hits, body.query)
        
    except UnexpectedResponse as e:
        code = getattr(e, "status_code", None)
        raise HTTPException(status_code=502, detail=f"Qdrant search error: {code} {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"search error: {type(e).__name__}: {e}")

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


    

