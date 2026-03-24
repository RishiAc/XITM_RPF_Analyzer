import os
import re
import json
import logging
import openai
from openai import RateLimitError, APIError, APIConnectionError
from fastapi import APIRouter, HTTPException
from .models import BatchOrchestrateEvalBody, BatchQueryResult, BatchResponse
from typing import List, Dict, Any
from .vector_api import orchestrate_queries, OrchestrateBody
from supabase import create_client
from tenacity import (
    retry,
    stop_after_attempt,
    retry_if_exception_type,
    before_sleep_log,
    after_log
)
from langchain_core.runnables import RunnableLambda

# ---- Logging ----
logger = logging.getLogger(__name__)

# ---- Environment ----
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

router = APIRouter(prefix="/eval", tags=["LLM Evaluation"])

supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)


def dynamic_wait(retry_state):
    """Parse Retry-After from OpenAI errors; use 25s minimum for free tier (3 RPM)."""
    exc = retry_state.outcome.exception()
    error_str = str(exc)
    
    # Parse "try again in Xh Xm Xs" from error message
    hours = minutes = seconds = 0
    if h := re.search(r'(\d+)h', error_str): hours = int(h.group(1))
    if m := re.search(r'(\d+)m', error_str): minutes = int(m.group(1))
    if s := re.search(r'(\d+(?:\.\d+)?)s', error_str): seconds = float(s.group(1))
    retry_after = hours * 3600 + minutes * 60 + seconds
    
    # Use Retry-After if reasonable (<2 min), otherwise exponential backoff
    attempt = retry_state.attempt_number
    if 0 < retry_after < 120:
        wait = retry_after + 1
    else:
        wait = min(25 * (2 ** (attempt - 1)), 120)  # 25s base for free tier, max 120s
    
    logger.info(f"Rate limited. Waiting {wait:.1f}s (attempt {attempt}, retry_after={retry_after:.1f}s)")
    return wait


@retry(
    retry=retry_if_exception_type((RateLimitError, APIError, APIConnectionError)),
    wait=dynamic_wait,
    stop=stop_after_attempt(15),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    after=after_log(logger, logging.INFO),
    reraise=True
)
def _process_batch(batch_queries: List[Dict[str, Any]]) -> BatchResponse:
    """
    Process a batch of queries in a single OpenAI API call.
    Each query is tagged as either 'evaluate' or 'summarize'.
    Returns structured BatchResponse with results for each query.
    
    Dynamically waits based on OpenAI's Retry-After header. Uses 25s minimum
    for free tier (3 RPM). Retries up to 15 times on rate limit errors.
    """
    # Build the JSON payload for the batch
    batch_payload = {"queries": batch_queries}
    
    system_prompt = """You are a business development analyst for an IT government contracting firm processing multiple queries about RFP documents.

You will receive a JSON object with an array of queries. Each query has:
- query_number: unique identifier
- task: either "evaluate" or "summarize"
- rfp_query_text: the original query
- rfp_excerpts: relevant excerpts from the RFP document
- knowledge_base_answer: (only for "evaluate" tasks) the firm's capabilities to evaluate
- company_evidence: (only for "evaluate" tasks) pre-retrieved excerpts from company internal documents

### Ground Rules:
1. You MUST base your response solely on the rfp_excerpts provided for each query.
2. Assume the person reading your response does not have the RFP document. You MUST quote specific text from the excerpts.
3. Your responses should be as specific and verbose as possible, citing exact phrases, requirements, dates, or specifications from the excerpts.
4. Include direct quotes from the excerpts to support your analysis.

### For "evaluate" tasks:
You will receive:
- rfp_excerpts: Relevant excerpts from the RFP document (retrieved live)
- knowledge_base_answer: Direct answer provided by the user (if any)
- company_evidence: Pre-retrieved excerpts from company internal documents

Evaluate alignment considering the firm's capabilities from BOTH knowledge_base_answer AND company_evidence against the RFP requirements.

Rate alignment from 1-5:
1 = No alignment - the firm's capabilities do not address any RFP requirements
2 = Weakly related - minimal overlap between capabilities and requirements
3 = Some relevant overlap - partial alignment with gaps
4 = Strong alignment with minor gaps - most requirements addressed
5 = Fully aligned, comprehensive match - all requirements clearly addressed

Provide a detailed explanation citing specific quotes from the RFP excerpts that support your score. Explain exactly which requirements from the RFP are met or not met by the firm's capabilities.

### For "summarize" tasks:
Provide a comprehensive summary answering the query based on the excerpts. Include specific details, quotes, dates, requirements, and any relevant information found in the excerpts. Be thorough and verbose.

Process each query independently and return results in the same order."""

    user_prompt = f"""Process each query in this batch and return your analysis:

{json.dumps(batch_payload, indent=2)}

Return a JSON object with a "results" array containing one object per query with:
- query_number: the query's identifier
- task_type: "evaluate" or "summarize"
- score: (only for evaluate) integer 1-5
- explanation: (only for evaluate) detailed reasoning with specific quotes from the excerpts
- summary: (only for summarize) comprehensive summary with specific details and quotes from the excerpts"""

    completion = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2,
        response_format={"type": "json_object"}
    )

    response_text = completion.choices[0].message.content
    response_json = json.loads(response_text)
    
    # Parse into BatchResponse model
    results = []
    for item in response_json.get("results", []):
        results.append(BatchQueryResult(
            query_number=item.get("query_number"),
            task_type=item.get("task_type"),
            score=item.get("score"),
            explanation=item.get("explanation"),
            summary=item.get("summary")
        ))
    
    return BatchResponse(results=results)


process_batch_runnable = RunnableLambda(_process_batch)


@router.post("/batch-orchestrate-eval")
def batch_orchestrate_and_evaluate(body: BatchOrchestrateEvalBody):
    """
    Batched version of orchestrate-eval that groups multiple queries into single API calls.
    
    For each query:
      - if knowledge_base_answer exists -> tag as "evaluate" (compare and score)
      - else -> tag as "summarize" (generate summary)
    
    Processes queries in batches (default 4 per API call) to avoid rate limits.
    Writes results into Supabase RFP_Evals.
    """
    try:
        # 1) Build OrchestrateBody and call orchestrate_queries
        orch_body = OrchestrateBody(
            rfp_id=body.rfp_id,
            rfp_doc_id=body.rfp_doc_id,
            top_k=body.top_k,
            query_numbers=body.query_numbers
        )
        orch = orchestrate_queries(orch_body)
        queries = orch.get("queries", [])
        
        if not queries:
            raise HTTPException(status_code=400, detail="No queries found")
        
        k = body.top_k or 20  # Match chat feature's top_k
        batch_size = body.batch_size or 2  # Default 2 for free tier; increase to 4+ on paid tier
        
        # 2) Prepare queries with task tags
        tagged_queries = []
        query_metadata = {}  # Store original query data for Supabase writes
        
        for q in queries:
            qnum = q.get("query_number")
            rq = q.get("rfp_query_text", "")
            kb = (q.get("knowledge_base_answer") or "").strip()
            company_evidence = q.get("knowledge_base_chunks", []) or []
            topk = q.get("rfp_topk", []) or []
            
            # Extract excerpts (full text, no truncation)
            excerpts = [t.get("text", "") for t in topk[:k]]
            
            # Store metadata for later Supabase writes
            query_metadata[qnum] = {
                "rfp_query_text": rq,
                "query_phase": q.get("query_phase"),
                "weight": q.get("weight"),
                "rfp_topk": topk,
                "knowledge_base_answer": kb if kb else None,
                "company_evidence": company_evidence,
            }
            
            # Evaluate if we have manual answer OR pre-computed company evidence
            has_evidence = kb or (isinstance(company_evidence, list) and len(company_evidence) > 0)
            
            # Build tagged query for batch processing
            if has_evidence:
                tagged_queries.append({
                    "query_number": qnum,
                    "task": "evaluate",
                    "rfp_query_text": rq,
                    "knowledge_base_answer": kb,
                    "company_evidence": company_evidence,
                    "rfp_excerpts": excerpts
                })
            else:
                tagged_queries.append({
                    "query_number": qnum,
                    "task": "summarize",
                    "rfp_query_text": rq,
                    "rfp_excerpts": excerpts
                })
        
        # 3) Process batches in parallel via LangChain batch()
        batch_inputs = [
            tagged_queries[i:i + batch_size]
            for i in range(0, len(tagged_queries), batch_size)
        ]
        batch_responses = process_batch_runnable.batch(
            batch_inputs,
            config={"max_concurrency": 5}
        )
        all_results = [r for resp in batch_responses for r in resp.results]
        
        # 4) Build response and write to Supabase
        final_results = []
        for result in all_results:
            qnum = result.query_number
            meta = query_metadata.get(qnum, {})
            company_evidence = meta.get("company_evidence") or []
            
            item = {
                "query_number": qnum,
                "rfp_query_text": meta.get("rfp_query_text", ""),
                "query_phase": meta.get("query_phase"),
                "weight": meta.get("weight"),
                "rfp_topk": meta.get("rfp_topk", []),
            }
            
            if result.task_type == "evaluate":
                item.update({
                    "knowledge_base_answer": meta.get("knowledge_base_answer"),
                    "evaluation": {
                        "score": result.score,
                        "explanation": result.explanation
                    }
                })
                llm_answer = result.explanation or ""
                score = result.score or 1
            else:
                item.update({
                    "generated_summary": result.summary
                })
                llm_answer = result.summary or ""
                score = 1  # default for summaries

            # Persist only the manual knowledge base answer for display.
            # Retrieved company evidence should not be shown as KB answer text.
            persisted_kb_chunk = meta.get("knowledge_base_answer")
            
            final_results.append(item)
            
            # Write to Supabase RFP_Evals (upsert to replace existing evaluations)
            upsert_json = {
                "rfp_id": body.rfp_doc_id,
                "query_number": qnum,
                "query_text": meta.get("rfp_query_text", ""),
                "query_llm_answer": llm_answer,
                "score": score,
                "rfp_citation_chunks": [t.get("text", "") for t in meta.get("rfp_topk", [])],
                "knowledge_base_chunk": persisted_kb_chunk,
                "query_phase": meta.get("query_phase"),
            }
            supabase_client.table("RFP_Evals").upsert(upsert_json, on_conflict="rfp_id,query_number").execute()
        
        return {
            "rfp_id": body.rfp_id,
            "total_queries": len(final_results),
            "batch_size": batch_size,
            "batches_processed": (len(tagged_queries) + batch_size - 1) // batch_size,
            "queries": final_results,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"batch-orchestrate-eval error: {e}")


@router.get("/get-evals")
def get_existing_evaluations(rfp_id: str):
    """
    Fetch existing evaluations from Supabase RFP_Evals table.
    Returns evaluations in the same format as batch-orchestrate-eval,
    along with calculated scores.
    """
    try:
        # Query RFP_Evals table for this RFP
        response = (
            supabase_client
            .table("RFP_Evals")
            .select("query_number, query_text, query_llm_answer, score, query_phase, rfp_citation_chunks, knowledge_base_chunk")
            .eq("rfp_id", rfp_id)
            .order("query_number")
            .execute()
        )
        
        if not response.data:
            return {
                "rfp_id": rfp_id,
                "total_queries": 0,
                "queries": [],
                "scores": None
            }
        
        # Determine which query_numbers are evidence-backed in Query_Table_duplicate.
        # This allows correct evaluate/summarize reconstruction even when
        # RFP_Evals.knowledge_base_chunk is null in older rows.
        qnums = [row.get("query_number") for row in (response.data or []) if row.get("query_number") is not None]
        evidence_map = {}
        kb_answer_map = {}
        kb_chunks_map = {}
        if qnums:
            qt = (
                supabase_client
                .table("Query_Table_duplicate")
                .select("query_number, knowledge_base_answer, knowledge_base_chunks")
                .in_("query_number", qnums)
                .execute()
            )
            for r in (qt.data or []):
                kb_ans = (r.get("knowledge_base_answer") or "").strip()
                kb_chunks = r.get("knowledge_base_chunks") or []
                qn = r.get("query_number")
                kb_answer_map[qn] = kb_ans
                kb_chunks_map[qn] = kb_chunks if isinstance(kb_chunks, list) else []
                evidence_map[r.get("query_number")] = bool(
                    kb_ans or (isinstance(kb_chunks, list) and len(kb_chunks) > 0)
                )

        # Transform rows into frontend format (matching batch-orchestrate-eval output)
        queries = []
        phase_totals = {1: {"sum": 0, "count": 0}, 2: {"sum": 0, "count": 0}, 
                        3: {"sum": 0, "count": 0}, 4: {"sum": 0, "count": 0}}
        
        for row in response.data:
            query_phase = row.get("query_phase") or 1
            score = row.get("score") or 1
            llm_answer = row.get("query_llm_answer") or ""
            has_evidence = bool(evidence_map.get(row.get("query_number")))
            
            # Build query item in same format as batch-orchestrate-eval
            item = {
                "query_number": row.get("query_number"),
                "rfp_query_text": row.get("query_text") or "",
                "query_phase": query_phase,
                "rfp_topk": [{"text": chunk} for chunk in (row.get("rfp_citation_chunks") or [])],
            }
            
            # If evidence exists (manual KB answer and/or company evidence), this is evaluate.
            if has_evidence:
                # Display only the manual answer entered on Knowledge Base page.
                display_kb = (kb_answer_map.get(row.get("query_number")) or "").strip()
                if display_kb:
                    item["knowledge_base_answer"] = display_kb
                item["evaluation"] = {
                    "score": score,
                    "explanation": llm_answer
                }
            else:
                # This was a "summarize" task
                item["generated_summary"] = llm_answer
            
            queries.append(item)
            
            # Accumulate for score calculation
            if 1 <= query_phase <= 4:
                phase_totals[query_phase]["sum"] += score
                phase_totals[query_phase]["count"] += 1
        
        # Calculate phase scores (average score per phase)
        phase_scores = {}
        total_sum = 0
        total_count = 0
        for phase_num in range(1, 5):
            pt = phase_totals[phase_num]
            if pt["count"] > 0:
                phase_scores[f"phase{phase_num}"] = pt["sum"] / pt["count"]
                total_sum += pt["sum"]
                total_count += pt["count"]
            else:
                phase_scores[f"phase{phase_num}"] = 0.0
        
        phase_scores["total"] = total_sum / total_count if total_count > 0 else 0.0
        
        return {
            "rfp_id": rfp_id,
            "total_queries": len(queries),
            "queries": queries,
            "scores": phase_scores
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"get-evals error: {e}")
