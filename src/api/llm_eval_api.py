import os
import json
import openai
import psycopg2
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional

# ---- Environment ----
OPENAI_API_KEY = "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"
DB_URL = os.getenv("DATABASE_URL")
VECTOR_API_URL = "http://localhost:8000/vector/search"
MOCK_DB = True

if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

router = APIRouter(prefix="/eval", tags=["LLM Evaluation"])

# ---- Database Helper ----
def get_db_conn():
    if MOCK_DB:
        return None
    try:
        conn = psycopg2.connect(DB_URL)
        conn.autocommit = True
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")

# ---- Request Models ----
class EvalRequest(BaseModel):
    rfp_id: str
    query_number: int
    query_text: str
    qa_answer: str
    top_k: Optional[int] = 5  # how many chunks to retrieve

# ---- OpenAI Scoring ----
@router.post("/llm-eval")
def evaluate_llm_test():
    """
    Temporary hardcoded version — no vector search.
    Just compares one fixed firm answer and RFP excerpts.
    """

    qa_answer = """
    Our company provides minimal SIEM monitoring, incident response,
    and cloud infrastructure threat detection across AWS and Azure environments.
    """

    retrieved_texts = [
        "The contractor shall provide continuous threat monitoring and intrusion detection services.",
        "The contractor shall maintain SIEM-based alerts and reporting 24/7.",
        "The contractor shall support multiple cloud environments, including AWS and Azure."
    ]

    prompt = f"""
You are evaluating how well a firm's capabilities align with the RFP requirements.

Rate from 1–5:
5 = No alignment
4 = Weakly related
3 = Some relevant overlap
2 = Strong alignment with minor gaps
1 = Fully aligned, comprehensive match

Return JSON only:
{{"score": <int>, "explanation": "<brief reasoning>"}}

Firm Capabilities:
{qa_answer}

RFP Statement of Work excerpts:
{chr(10).join(['- ' + t for t in retrieved_texts])}
"""

    try:
        completion = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        text = completion.choices[0].message.content.strip()
        return json.loads(text)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {e}")
