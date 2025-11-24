from pydantic import BaseModel
from typing import Optional, List, Dict, Union

class SearchBody(BaseModel):
    doc_id: str
    query: str
    top_k: Optional[int] = 5

class EvaluateRequest(BaseModel):
    doc_id: str
    query: str
    top_k: Optional[int] = 5
    qa_answer: str