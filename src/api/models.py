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


# ---- Batch Evaluation Models ----

class BatchOrchestrateEvalBody(BaseModel):
    rfp_id: str
    rfp_doc_id: str
    top_k: Optional[int] = 5
    batch_size: Optional[int] = 4  # queries per API call
    query_numbers: Optional[List[int]] = None


class BatchQueryResult(BaseModel):
    query_number: int
    task_type: str  # "evaluate" or "summarize"
    score: Optional[int] = None  # 1-5 for evaluation
    explanation: Optional[str] = None  # for evaluation
    summary: Optional[str] = None  # for summarization


class BatchResponse(BaseModel):
    results: List[BatchQueryResult]