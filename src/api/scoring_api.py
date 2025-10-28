from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from vector_api import OrchestrateBody, orchestrate_queries
from pydantic import BaseModel
import numpy as np

router = APIRouter(prefix="/score", tags=["score"])

class QueryPair(BaseModel):
    kb_answer: str
    rfp_query_text: str
    rfp_query_embedding: list[float]

# because we are using the same model across services (upserting into db and embedding chunks and questions)
# I am assuming the dimensions are the same in this method\

# TODO: Have a more strict check of dimensions and vectors across code
def _cosine_similarity(v1, v2):
    a = np.array(v1, dtype=float)
    b = np.array(v2, dtype=float)

    cos_sim = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    return cos_sim

def _calculate_score(body: OrchestrateBody):

    tests = orchestrate_queries(body)

    score = 0

    for test in tests["queries"]:
        query_number = test["query_number"]
        question = test["rfp_query_text"]
        ans = test["knowledge_base_answer"]
        ans_embedding = test["knowledge_base_answer_embedding"]
        weight = test["weight"]

        rfp_chunks = test["rfp_topk"]

        # assuming chunks are qdrant scored point objects
        for chunk in rfp_chunks:
            chunk_embedding = chunk.vector
            chunk_text = chunk.payload["text"]
            chunk_page_num = chunk.payload["page_num"]

            # compute the similarity score
            cos_sim = _cosine_similarity(list(chunk_embedding), list(ans_embedding))

            # TODO: use an NLI model to compute hypothesis pairs

            score += cos_sim * weight

    return score

@router.post("/score-rfp")
def score_rfp(body: OrchestrateBody):

    score = _calculate_score(body)

    return {
        "score": max(0, score)
    }