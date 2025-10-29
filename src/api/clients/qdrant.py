import os
from qdrant_client import QdrantClient, models

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "rfp_chunks")

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