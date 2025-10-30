import os
import json
import openai
import psycopg2
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from .vector_api import search, SearchBody
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
class EvaluateRequest(BaseModel):
    doc_id: str
    query: str
    top_k: Optional[int] = 5
    qa_answer: str


@router.post("/llm-eval")
def evaluate_llm_test(body: EvaluateRequest):
    """
    Evaluate how well a firm's QA answer aligns with the top-k RFP text segments.
    """

    try:
        # 1️⃣ Build SearchBody and run vector search
        search_body = SearchBody(
            doc_id=body.doc_id,
            query=body.query,
            top_k=body.top_k
        )
        search_results = search(search_body)  # [(hit, score), ...]

        # 2️⃣ Slice to top_k results (in case rerank returns extras)
        top_hits = search_results[:body.top_k]

        # 3️⃣ Extract only the text from each top hit
        retrieved_texts = []
        for hit, score in top_hits:
            text = (hit.payload or {}).get("text", "")
            retrieved_texts.append(text[:500])  # keep first 500 chars for clarity

        # 4️⃣ Build evaluation prompt for LLM
        prompt = f"""
You are evaluating how well a firm's capabilities align with the RFP requirements.

Rate from 1–5:
1 = No alignment
2 = Weakly related
3 = Some relevant overlap
4 = Strong alignment with minor gaps
5 = Fully aligned, comprehensive match

Return JSON only:
{{"score": <int>, "explanation": "<brief reasoning>"}}

Firm Capabilities:
{body.qa_answer}

RFP Statement of Work excerpts:
{chr(10).join(['- ' + t for t in retrieved_texts])}
"""

        # 5️⃣ Call OpenAI for evaluation
        completion = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )

        text = completion.choices[0].message.content.strip()
        return json.loads(text)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {e}")
