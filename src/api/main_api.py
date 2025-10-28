from . import vector_api, chunk_api
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="XITM RFP API", version="0.0.2")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(vector_api.router)
app.include_router(chunk_api.router)

