from .vector_api import IngestBody, ingest_chunks
from .pdf.parser import parse, chunks_to_json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/chunk", tags=["chunk"])

class UploadBody(BaseModel):
    file: str
    doc_id: str

@router.post("/upload-pdf")
async def upload_pdf(body: UploadBody):
    try:
        # Convert PDF to chunks
        chunks = parse(body.file)

        # Convert PDF to JSON
        json_chunks = chunks_to_json(body.doc_id, chunks)["chunks"]

        # Convert JSON into IngestBody
        ingest_body = IngestBody(doc_id=body.doc_id, chunks=json_chunks)

        # Call your existing function
        result = ingest_chunks(ingest_body)

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
