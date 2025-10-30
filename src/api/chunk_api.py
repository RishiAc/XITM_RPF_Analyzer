from vector_api import IngestBody, ingest_chunks
from pdf.parser import parse, chunks_to_json
from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from tempfile import NamedTemporaryFile
from clients.supabase import _sb

router = APIRouter(prefix="/chunk", tags=["chunk"])

@router.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...), doc_id: str = Form(...)):
    try:
        # Temporarily save file
        temp_file = NamedTemporaryFile(suffix=".pdf")
        temp_file.write(await file.read())
        temp_path = temp_file.name

        # Convert PDF to chunks
        chunks = parse(temp_path)

        # Convert PDF to JSON
        json_chunks = chunks_to_json(doc_id, chunks)["chunks"]
        
        # Convert JSON into IngestBody
        ingest_body = IngestBody(doc_id=doc_id, chunks=json_chunks)

        # Call your existing function
        result = ingest_chunks(ingest_body)


    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Close temp_file
        temp_file.close()
        return result