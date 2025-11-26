from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from supabase import create_client
from typing import Optional
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

query_table = create_client(SUPABASE_URL, SUPABASE_KEY).table("Query_Table")
router = APIRouter(prefix="/knowledge_base", tags=["knowledge_base"])

class CreateBody(BaseModel):
    query_number: Optional[int] = None
    knowledge_base_answer: str
    rfp_query_text: str
    weight: float
    query_phase: int

class UpdateBody(BaseModel):
    query_number: int
    knowledge_base_answer: Optional[str] = None
    rfp_query_text: Optional[str] = None
    weight: Optional[float] = None
    query_phase: Optional[int] = None

@router.post("/create_query_row")
async def create_query_row(body: CreateBody):
    """
    Creates and inserts a row in Query_Table with the given information

    Arguments are given in a json format
    Args:
        query_number (Optional[int]): query number for this query, if not given one will be automatically assigned
        knowledge_base_answer (str): the given answer for this query to store in the knowledge base
        rfp_query_text (str): the actual query that was answered by the client
        weight (float): the importance of this query
        query_phase (int): the phase this query is a part of
    Returns:
        the response given by the supabase api
    """
    try:
        create_json = {
            "knowledge_base_answer": body.knowledge_base_answer,
            "rfp_query_text": body.rfp_query_text,
            "weight": body.weight,
            "query_phase": body.query_phase
        }
        if body.query_number != None:
            create_json["query_number"] = body.query_number

        return query_table.insert(create_json).execute()
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update_query_row")
async def update_query_row(body: UpdateBody):
    """
    Updates the row in Query_Table with given query_number using the given information,
    if any information is None, that coulumn's data will not be changed

    Arguments are given in a json format
    Args:
        query_number (int): the number of the query to be updated
        knowledge_base_answer (Optional[str]): the new knowledge_base_answer for the row, this column will not be changed if this argument is not given
        rfp_query_text (Optional[str]): the new rfp_query_text for the row, this column will not be changed if this argument is not given
        weight (Optional[float]): the new weight for the row, this column will not be changed if this argument is not given
        query_phase (Optional[int]): the new phase for this query
    Returns:
        the response given by the supabase api
    """
    try:
        # Construct update json based on given rows
        update_json = {}
        if body.knowledge_base_answer != None:
            update_json["knowledge_base_answer"] = body.knowledge_base_answer
        if body.rfp_query_text != None:
            update_json["rfp_query_text"] = body.rfp_query_text
        if body.weight != None:
            update_json["weight"] = body.weight
        if body.query_phase != None:
            update_json["query_phase"] = body.query_phase

        # Update row
        return query_table.update(update_json).eq("query_number", body.query_number).execute()
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/delete_query_row/{query_number}")
async def delete_query_row(query_number: int):
    """
    Deletes the row in Query_Table with given query_number

    Args:
        query_number (int): the number of the query to delete
    Returns:
        the response given by the supabase api
    """
    try:
        return query_table.delete().eq("query_number", query_number).execute()
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/select_query_row/{query_number}")
async def select_query_row(query_number: int):
    """
    Runs a select query to get the row in Query_Table with the given query_number

    Args:
        query_number (int): the number of the query to select
    Returns:
        the response given by the supabase api, in this case, the requested row
    """
    try:
        return query_table.select("*").eq("query_number", query_number).execute()
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/get_all_query_rows")
async def get_all_query_rows():
    """
    Returns all rows in Query_Table.

    Returns:
        The response from the Supabase API containing all rows.
    """
    try:
        return query_table.select("*").execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))