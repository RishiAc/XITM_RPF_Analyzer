from fastapi import APIRouter
from api.vector_api import OrchestrateBody, orchestrate_queries
from pydantic import BaseModel
import numpy as np
from api.clients.supabase import _sb
from api.clients.openai import get_chat_completion

router = APIRouter(prefix="/score", tags=["score"])

class RfpEval(BaseModel):
    query_number: int
    score: int
    phase: int
    weight: int

class RfpScore(BaseModel):
    phase1: float
    phase2: float
    phase3: float
    phase4: float
    total: float

def _get_evals(rfp_id: str) -> list[RfpEval]:
    evals = []
    response = (
        _sb
        .table("RFP_Evals")          # or .from_("users") in older versions
        .select("query_number, score, query_phase, weight:query_number(weight)")             # or "id, name, email" for specific columns
        .eq("rfp_id", rfp_id)       # <-- filter where id == user_id
        .execute()
    )

    print(response.data[0])  # list of matching rows

    result = response.data

    for row in result:
        evals.append(RfpEval(
            query_number=row["query_number"],
            score=row["score"],
            phase=row["query_phase"],
            weight=row["weight"]["weight"]
        ))
    
    return evals

def _caculate_score(evals: list[RfpEval]) -> RfpScore:
    tracker = [
        {
            "total": 0,
            "weight": 0
        }
        for _ in range(4)
    ]

    for e in evals:
        idx = e.phase - 1
        tracker[idx]["total"] += e.score * e.weight
        tracker[idx]["weight"] += e.weight
    
    total = sum([t["total"] for t in tracker])
    total_weight = sum([t["weight"] for t in tracker])

    return RfpScore(
        phase1=tracker[0]["total"] / tracker[0]["weight"],
        phase2=tracker[1]["total"] / tracker[1]["weight"],
        phase3=tracker[2]["total"] / tracker[2]["weight"],
        phase4=tracker[3]["total"] / tracker[3]["weight"],
        total=total / total_weight
    )


@router.post("/score-rfp")
def score_rfp(rfp_id: str):
    try:
        evals = _get_evals(rfp_id)
        score = _caculate_score(evals)
        return score, 200
    except Exception as e:
        return { "error": e }, 400
