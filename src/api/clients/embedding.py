import os
from sentence_transformers import SentenceTransformer

EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

_app_embedding_model = SentenceTransformer(EMBED_MODEL)

