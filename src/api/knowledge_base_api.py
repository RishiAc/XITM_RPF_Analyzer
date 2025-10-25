from fastapi import APIRouter
from pydantic import BaseModel
from supabase import create_client, Client
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
router = APIRouter(prefix="/knowledge_base", tags=["knowledge_base"])

class CreateBody(BaseModel):
    knowledge_base_answer: str
    rfp_query_text: str
    weight: float

class UpdateBody(BaseModel):
    query_number: int
    knowledge_base_answer: str | None
    rfp_query_text: str | None
    weight: float | None

class DeleteBody(BaseModel):
    query_number: int

@router.post("/creat_query_row")
async def create_query_row(body: CreateBody):
    """Creates and inserts a row in Query_Table with the given information"""

    supabase_client.table("Query_Table").insert({
        "knowledge_base_answer": body.knowledge_base_answer,
        "rfp_query_text": body.rfp_query_text,
        "weight": body.weight
    }).execute()

@router.post("/update_query_row")
async def update_query_row(body: UpdateBody):
    """Updates the row in Query_Table with given query_number using the given information,
    if any information is None, that coulumn's data will not be changed"""

    # Construct update json based on given rows
    update_json = {}
    if body.knowledge_base_answer != None:
        update_json["knowledge_base_answer"] = body.knowledge_base_answer
    if body.rfp_query_text != None:
        update_json["rfp_query_text"] = body.rfp_query_text
    if body.weight != None:
        update_json["weigth"] = body.weight

    # Update row
    supabase_client.table("Query_Table").update(update_json).eq("query_number", body.query_number).execute()

@router.post("/delete_query_row")
async def delete_query_row(body: DeleteBody):
    supabase_client.table("Query_Table").delete().eq("query_number", body.query_number).execute()