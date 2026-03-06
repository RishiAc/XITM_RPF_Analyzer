from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from .clients.supabase import _sb

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
        .table("RFP_Evals")
        .select("query_number, score, query_phase, weight:query_number(weight)")
        .eq("rfp_id", rfp_id)
        .execute()
    )

    if not response.data:
        return []

    for row in response.data:
        # Handle case where weight might be None or nested
        weight_val = 1
        if row.get("weight"):
            if isinstance(row["weight"], dict):
                weight_val = row["weight"].get("weight", 1)
            else:
                weight_val = row["weight"]
        
        evals.append(RfpEval(
            query_number=row["query_number"],
            score=row["score"],
            phase=row["query_phase"],
            weight=weight_val
        ))
    
    return evals


def _calculate_score(evals: list[RfpEval]) -> RfpScore:
    tracker = [
        {"total": 0, "weight": 0}
        for _ in range(4)
    ]

    for e in evals:
        # Ensure phase is within valid range (1-4)
        if 1 <= e.phase <= 4:
            idx = e.phase - 1
            tracker[idx]["total"] += e.score * e.weight
            tracker[idx]["weight"] += e.weight
    
    # Calculate phase scores (handle division by zero)
    phase_scores = []
    for t in tracker:
        if t["weight"] > 0:
            phase_scores.append(t["total"] / t["weight"])
        else:
            phase_scores.append(0.0)
    
    total = sum(t["total"] for t in tracker)
    total_weight = sum(t["weight"] for t in tracker)
    overall = total / total_weight if total_weight > 0 else 0.0

    return RfpScore(
        phase1=phase_scores[0],
        phase2=phase_scores[1],
        phase3=phase_scores[2],
        phase4=phase_scores[3],
        total=overall
    )


def _update_rfp_scores(rfp_id: str, scores: RfpScore):
    """Update RFPs table with calculated scores (converted to 0-100 scale)."""
    _sb.table("RFPs").update({
        "overall_score": round(scores.total * 20, 1),  # 1-5 -> 0-100
        "P1": round(scores.phase1 * 20),
        "P2": round(scores.phase2 * 20),
        "P3": round(scores.phase3 * 20),
        "P4": round(scores.phase4 * 20),
    }).eq("qdrant_doc_id", rfp_id).execute()


@router.post("/score-rfp")
def score_rfp(rfp_id: str):
    """
    Calculate and persist RFP scores.
    Returns scores on 1-5 scale for each phase and overall.
    """
    try:
        evals = _get_evals(rfp_id)
        
        if not evals:
            raise HTTPException(status_code=404, detail=f"No evaluations found for rfp_id={rfp_id}")
        
        scores = _calculate_score(evals)
        
        # Persist scores to RFPs table
        _update_rfp_scores(rfp_id, scores)
        
        return scores
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Score calculation failed: {e}")
