from fastapi import APIRouter, File, UploadFile, HTTPException
from tempfile import NamedTemporaryFile
from supabase import create_client, Client
from .vector_api import IngestBody, ingest_chunks
from .pdf.parser import parse, chunks_to_json
import os

router = APIRouter(prefix="/chunk", tags=["chunk"])

# Initialize Supabase client using your frontend-style env vars
SUPABASE_URL = os.getenv("REACT_APP_SUPABASE_URL")
SUPABASE_KEY = os.getenv("REACT_APP_SUPABASE_ANON_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@router.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        # 1️⃣ Save PDF temporarily
        temp_file = NamedTemporaryFile(suffix=".pdf", delete=False)
        temp_file.write(await file.read())
        temp_file.close()
        temp_path = temp_file.name
        filename = file.filename

        # 2️⃣ Insert into Supabase (autogenerate UUID id)
        insert_resp = supabase.table("RFPs").insert({
            "name": filename
        }).execute()

        if not insert_resp.data:
            raise HTTPException(status_code=500, detail="Failed to insert RFP record")

        rfp = insert_resp.data[0]
        id_ = str(rfp["id"])
        qdrant_doc_id = id_

        # 3️⃣ Update record to include qdrant_doc_id
        supabase.table("RFPs").update({"qdrant_doc_id": qdrant_doc_id}).eq("id", id_).execute()

        # 4️⃣ Parse + chunk the PDF
        chunks = parse(temp_path)
        json_chunks = chunks_to_json(qdrant_doc_id, chunks)["chunks"]

        # 5️⃣ Ingest into Qdrant using qdrant_doc_id
        ingest_body = IngestBody(doc_id=qdrant_doc_id, chunks=json_chunks)
        result = ingest_chunks(ingest_body)

        # 6️⃣ Return metadata for frontend
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
