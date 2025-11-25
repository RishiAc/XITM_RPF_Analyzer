from . import query_table_api, vector_api, chunk_api, llm_eval_api, query_api
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="XITM RFP API", version="0.0.2")

app.add_middleware(
    CORSMiddleware,
    # Loosen CORS for local dev so preflight never blocks chat requests
    allow_origins=["*"],
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(vector_api.router)
app.include_router(chunk_api.router)
app.include_router(query_table_api.router)
app.include_router(llm_eval_api.router)
app.include_router(query_api.router)


@app.get("/health")
def health():
    return {"ok": True}
