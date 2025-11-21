import os
import json
import openai
import psycopg2
import re
from fastapi import APIRouter, HTTPException
from .models import SearchBody, EvaluateRequest  # Updated import
from fastapi import APIRouter, HTTPException
import re, json
from .vector_api import orchestrate_queries, search, OrchestrateBody  # import search/orchestrator here
from supabase import create_client

# ---- Environment ----
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DB_URL = os.getenv("SUPABASE_URL")
VECTOR_API_URL = "http://localhost:8000/vector/search"
MOCK_DB = True
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

router = APIRouter(prefix="/eval", tags=["LLM Evaluation"])

supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)

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
        search_results = search(search_body)  # Now returns list of dicts

        # 2️⃣ Slice to top_k results (in case rerank returns extras)
        top_hits = search_results[:body.top_k]

        # 3️⃣ Extract text from each result dictionary
        retrieved_texts = []
        for hit in top_hits:
            text = hit.get("text", "")
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

        text = completion.choices[0].message.content
        m = re.search(r'(\{.*"score".*\})', text, re.S)
        if not m:
            raise ValueError("Could not parse LLM response as JSON")
        return json.loads(m.group(1))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {e}")

@router.post("/orchestrate-eval")
def orchestrate_and_evaluate(body: OrchestrateBody):
    """
    Calls vector.orchestrate-queries and for each query:
      - if knowledge_base_answer exists -> call evaluate_llm_test to score
      - else -> generate a concise summary of top-k matches
    """
    try:
        orch = orchestrate_queries(body)
        queries = orch.get("queries", [])
        results = []
        for q in queries:
            qnum = q.get("query_number")
            rq = q.get("rfp_query_text", "")
            kb = (q.get("knowledge_base_answer") or "").strip()
            topk = q.get("rfp_topk", []) or []
            item = {
                "query_number": qnum,
                
                "rfp_query_text": rq,
                "query_phase": q.get("query_phase"),
                "weight": q.get("weight"),
                "rfp_topk": topk,
            }
            if kb:
                # build EvaluateRequest and call existing evaluator
                try:
                    eval_req = EvaluateRequest(doc_id=body.rfp_doc_id, query=rq, qa_answer=kb, top_k=body.top_k)
                    eval_res = evaluate_llm_test(eval_req)
                    item.update({
                        "knowledge_base_answer": kb,
                        "evaluation": eval_res
                    })
                except Exception as e:
                    item.update({"evaluation_error": str(e)})
            else:
                # summarize top-k via OpenAI
                try:
                    excerpts = [t.get("text", "") for t in topk[: body.top_k or 5]]
                    prompt = f"Summarize in 1-3 sentences the relevant points from these excerpts for the query:\n\nQuery: {rq}\n\n" + "\n\n".join(excerpts)
                    completion = openai.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.0,
                    )
                    summary = completion.choices[0].message.content.strip()
                    item.update({"generated_summary": summary})
                except Exception as e:
                    item.update({"summary_error": str(e)})
            results.append(item)
        return_val = {"rfp_id": body.rfp_id, "total_queries": len(results), "queries": results}

        # Update Supabase RFP_Evals table
        for query in results:
            insert_json = {
                "rfp_id": body.rfp_doc_id,
                "query_number": query["query_number"],
                "query_text": query["rfp_query_text"],
                "query_llm_answer": query["evaluation"]["explanation"],
                "score": query["evaluation"]["score"],
                "rfp_citation_chunks": [topk["text"] for topk in query["rfp_topk"]],
                "knowledge_base_chunk": query.get("knowledge_base_answer"),
                "query_phase": query["query_phase"]
            }
            
            supabase_client.table("RFP_Evals").insert(insert_json).execute()

        return return_val
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"orchestrate-eval error: {e}")

