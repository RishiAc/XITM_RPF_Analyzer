# src/api/app.py
import os
import uuid
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse
# src/api/app.py (only showing the diffs/additions)
from qdrant_client.http.exceptions import UnexpectedResponse

# ---- env ----
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY") or None
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

def _embed(texts: List[str]) -> List[list[float]]:
    vecs = _app_model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
    return [v.tolist() for v in vecs]

app = FastAPI(title="XITM RFP API", version="0.0.2")

class IngestBody(BaseModel):
    doc_id: str
    chunks: List[str]

class SearchBody(BaseModel):
    doc_id: str
    query: str
    top_k: Optional[int] = 5

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/ingest-chunks")
def ingest_chunks(body: IngestBody):
    try:
        if not body.chunks:
            raise HTTPException(400, "chunks cannot be empty")

        vecs = _embed(body.chunks)
        dim = len(vecs[0])
        _ensure_collection(dim)

        # Use UUIDs for Qdrant point IDs (required: int or UUID)
        points = []
        for i, t in enumerate(body.chunks):
            pid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{body.doc_id}:{i}"))  # deterministic UUID
            vector = vecs[i] if isinstance(vecs[i], list) else vecs[i].tolist()
            points.append(
                models.PointStruct(
                    id=pid,
                    vector=vector,
                    payload={"doc_id": body.doc_id, "text": t},
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

@app.post("/search")
def search(body: SearchBody):
    try:
        qvec = _embed([body.query])[0]
        filt = models.Filter(
            must=[models.FieldCondition(key="doc_id", match=models.MatchValue(value=body.doc_id))]
        )
        hits = _client.search(
            collection_name=QDRANT_COLLECTION,
            query_vector=qvec,
            limit=body.top_k or 5,
            query_filter=filt,
            with_payload=True,
        )
        return {
            "results": [
                {
                    "score": h.score,
                    "text": (h.payload or {}).get("text", "")[:500],
                }
                for h in hits
            ]
        }
    except UnexpectedResponse as e:
        code = getattr(e, "status_code", None)
        raise HTTPException(status_code=502, detail=f"Qdrant search error: {code} {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"search error: {type(e).__name__}: {e}")