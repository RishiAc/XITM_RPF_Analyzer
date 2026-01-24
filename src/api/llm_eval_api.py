import os
import json
import openai
from fastapi import APIRouter, HTTPException
from .models import BatchOrchestrateEvalBody, BatchQueryResult, BatchResponse
from typing import List, Dict, Any
from .vector_api import orchestrate_queries, OrchestrateBody
from supabase import create_client
from tenacity import retry, stop_after_attempt, wait_random_exponential

# ---- Environment ----
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

router = APIRouter(prefix="/eval", tags=["LLM Evaluation"])

supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)


@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def _process_batch(batch_queries: List[Dict[str, Any]]) -> BatchResponse:
    """
    Process a batch of queries in a single OpenAI API call.
    Each query is tagged as either 'evaluate' or 'summarize'.
    Returns structured BatchResponse with results for each query.
    
    Uses exponential backoff with jitter (1-60s) and retries up to 6 times
    on rate limit or transient errors.
    """
    # Build the JSON payload for the batch
    batch_payload = {"queries": batch_queries}
    
    system_prompt = """You are an expert analyst processing multiple queries about RFP documents.
You will receive a JSON object with an array of queries. Each query has:
- query_number: unique identifier
- task: either "evaluate" or "summarize"
- rfp_query_text: the original query
- rfp_excerpts: relevant excerpts from the RFP document
- knowledge_base_answer: (only for "evaluate" tasks) the firm's capabilities to evaluate

For "evaluate" tasks:
Rate alignment from 1-5:
1 = No alignment
2 = Weakly related
3 = Some relevant overlap
4 = Strong alignment with minor gaps
5 = Fully aligned, comprehensive match
Provide a brief explanation of your reasoning.

For "summarize" tasks:
Provide a concise 1-3 sentence summary of the relevant points from the excerpts.

Process each query independently and return results in the same order."""

    user_prompt = f"""Process each query in this batch and return your analysis:

{json.dumps(batch_payload, indent=2)}

Return a JSON object with a "results" array containing one object per query with:
- query_number: the query's identifier
- task_type: "evaluate" or "summarize"
- score: (only for evaluate) integer 1-5
- explanation: (only for evaluate) brief reasoning
- summary: (only for summarize) 1-3 sentence summary"""

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
        
        k = body.top_k or 5
        batch_size = body.batch_size or 4
        
        # 2) Prepare queries with task tags
        tagged_queries = []
        query_metadata = {}  # Store original query data for Supabase writes
        
        for q in queries:
            qnum = q.get("query_number")
            rq = q.get("rfp_query_text", "")
            kb = (q.get("knowledge_base_answer") or "").strip()
            topk = q.get("rfp_topk", []) or []
            
            # Extract excerpts (truncate for token limits)
            excerpts = [t.get("text", "")[:500] for t in topk[:k]]
            
            # Store metadata for later Supabase writes
            query_metadata[qnum] = {
                "rfp_query_text": rq,
                "query_phase": q.get("query_phase"),
                "weight": q.get("weight"),
                "rfp_topk": topk,
                "knowledge_base_answer": kb if kb else None,
            }
            
            # Build tagged query for batch processing
            if kb:
                tagged_queries.append({
                    "query_number": qnum,
                    "task": "evaluate",
                    "rfp_query_text": rq,
                    "knowledge_base_answer": kb,
                    "rfp_excerpts": excerpts
                })
            else:
                tagged_queries.append({
                    "query_number": qnum,
                    "task": "summarize",
                    "rfp_query_text": rq,
                    "rfp_excerpts": excerpts
                })
        
        # 3) Process in batches
        all_results = []
        for i in range(0, len(tagged_queries), batch_size):
            batch = tagged_queries[i:i + batch_size]
            batch_response = _process_batch(batch)
            all_results.extend(batch_response.results)
        
        # 4) Build response and write to Supabase
        final_results = []
        for result in all_results:
            qnum = result.query_number
            meta = query_metadata.get(qnum, {})
            
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
            
            final_results.append(item)
            
            # Write to Supabase RFP_Evals
            insert_json = {
                "rfp_id": body.rfp_doc_id,
                "query_number": qnum,
                "query_text": meta.get("rfp_query_text", ""),
                "query_llm_answer": llm_answer,
                "score": score,
                "rfp_citation_chunks": [t.get("text", "") for t in meta.get("rfp_topk", [])],
                "knowledge_base_chunk": meta.get("knowledge_base_answer"),
                "query_phase": meta.get("query_phase"),
            }
            supabase_client.table("RFP_Evals").insert(insert_json).execute()
        
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
