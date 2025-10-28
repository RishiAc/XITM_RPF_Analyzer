import vector_api, chunk_api, scoring_api
from fastapi import FastAPI


app = FastAPI(title="XITM RFP API", version="0.0.2")

app.include_router(vector_api.router)
app.include_router(chunk_api.router)
app.include_router(scoring_api.router)