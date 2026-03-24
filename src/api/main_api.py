from dotenv import load_dotenv
load_dotenv()

import os
from . import query_table_api, vector_api, chunk_api, llm_eval_api, query_api, scoring_api, gdrive_api
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="XITM RFP API", version="0.0.2")

cors_origins_raw = os.getenv("CORS_ALLOWED_ORIGINS", "")
cors_allow_origins = [origin.strip() for origin in cors_origins_raw.split(",") if origin.strip()]
cors_allow_origin_regex = os.getenv("CORS_ALLOWED_ORIGIN_REGEX")

# Safe defaults for local development only.
if not cors_allow_origins and not cors_allow_origin_regex:
    cors_allow_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_allow_origins,
    allow_origin_regex=cors_allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True}

app.include_router(vector_api.router)
app.include_router(chunk_api.router)
app.include_router(query_table_api.router)
app.include_router(llm_eval_api.router)
app.include_router(query_api.router)
app.include_router(scoring_api.router)
app.include_router(gdrive_api.router)
