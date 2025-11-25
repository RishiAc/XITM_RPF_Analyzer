from fastapi import APIRouter
from api.vector_api import OrchestrateBody, orchestrate_queries
from pydantic import BaseModel
from api.clients.openai import get_chat_completion

router = APIRouter(prefix="/score", tags=["score"])

class ScoreResponse(BaseModel):
    score: int
    phase: int
    reasoning: str

class DisplayScores(BaseModel):
    phase_1: float
    phase_2: float
    phase_3: float
    phase_4: float
    total: float

def _get_scoring_prompt(rfp_chunks, question, expected_answer) -> str:
    prompt = f"""

        You are an AI assistant helping evaluate how well a given Request for Proposal (RFP) fits a specific company.

        You will be given:
        - A set of RFP text chunks.
        - A *question* describing a specific eligibility or fit criterion.
        - An *expected answer* representing the company's situation or capabilities.
        - A phase number indicating which stage of the evaluation pipeline this is.

        Your task:
        1. Carefully read the RFP chunks.
        2. Compare the RFP's requirements/constraints to the company's expected answer, *only* using the information in the chunks and the expected answer.
        3. Assign a single integer score from 1 to 10 indicating how well this RFP fits the company with respect to the given question.
        4. Return a JSON object that matches the following schema:

        ScoreResponse = {{
            "score": int,      // 1–10
            "phase": int,      // echo back the phase provided to you
            "reasoning": str   // concise explanation of *why* you chose that score
        }}

        SCORING RUBRIC (1–10)
        - 10: Perfect or near-perfect fit
        - The RFP requirements and the company's expected answer are fully aligned for this question.
        - No apparent conflicts, and the RFP explicitly supports the company's situation/capability.

        - 8–9: Strong fit
        - The RFP mostly aligns with the company's expected answer.
        - There may be small ambiguities or minor gaps, but nothing clearly disqualifying.

        - 6–7: Moderate / partial fit
        - Some requirements match the company's expected answer, but there are notable uncertainties, missing details, or potential concerns.
        - Fit is plausible but not clearly strong.

        - 4–5: Weak fit
        - Only limited alignment with the company's expected answer is evident in the RFP.
        - Important details are missing, vague, or appear somewhat mismatched.

        - 2–3: Very poor fit
        - The RFP appears largely incompatible with the company's expected answer.
        - Key requirements are likely unmet or contradicted by the company's situation.

        - 1: No fit / contradicting
        - The RFP explicitly requires something that clearly contradicts the company's expected answer, or the RFP very strongly implies the company is not eligible for this criterion.

        IMPORTANT INSTRUCTIONS
        - Use **only** the RFP chunks and the expected answer to justify your score.
        - Do **not** assume facts that are not in the provided text.
        - If the RFP does not mention anything relevant to the question, treat this as weak or unknown fit (typically in the 3–5 range), and explain that the RFP is silent or unclear.
        - Be explicit in your reasoning about:
        - Which parts of the RFP support or conflict with the company's situation.
        - Why those details lead to your chosen score bucket.

        INPUT
        RFP_CHUNKS:
        {rfp_chunks}

        QUESTION:
        "{question}"

        EXPECTED_ANSWER (Company’s situation/capability):
        "{expected_answer}"

        PHASE:
        {0}

        OUTPUT FORMAT
        Return **only** a single JSON object, with no extra text, exactly like this:

        {{
        "score": <integer 1-10>,
        "phase": <integer>,
        "reasoning": "<concise explanation>"
        }}
    """

    return prompt

def _calculate_score(chunks, question, answer) -> ScoreResponse:

    rfp_context = "\n".join(chunks)
    sys_prompt = """
        You are a precise RFP evaluation assistant. Your task is to analyze how well a company matches specific requirements of a Request for Proposal (RFP), one criterion at a time.

        You will receive:
        - Segmented text chunks from an RFP.
        - A question defining a specific eligibility or fit condition.
        - An expected answer describing the company’s capability or situation.
        - A phase number indicating the evaluation stage.

        You must:
        - Base all judgments ONLY on the provided RFP chunks and expected answer.
        - Avoid assumptions, speculation, or external knowledge.
        - Rate the fit strictly on a scale from **1 to 10 (inclusive)**.  
        ✔ **Score must always be an integer between 1 and 10 — never below 1 or above 10.**

        Guidelines:
        - A score of 10 represents a near-perfect match with explicit alignment.
        - A score of 1 represents direct contradiction or explicit non-eligibility.
        - If the RFP provides unclear, weak, or incomplete information, score proportionally lower (typically 3–5) and explain why.
        - Provide a brief, factual explanation using only evidence from the text.

        Your output must always follow the schema:
        {
        "score": int (1–10),
        "phase": int,
        "reasoning": str
        }

        Never include extra commentary outside the structured output.
    """
    prompt = _get_scoring_prompt(rfp_context, question, answer)
    response: ScoreResponse = get_chat_completion(
        system_message=sys_prompt,
        user_prompt=prompt,
        response_format=ScoreResponse
    )

    return response
    

@router.post("/score-rfp")
def score_rfp(body: OrchestrateBody):

    tests = orchestrate_queries(body)

    all_scores = [[], [], [], []]
    final_scores = [[], [], [], []]

    for test in tests["queries"]:
        query_number = test["query_number"]
        query_phase = test["query_phase"]
        question = test["rfp_query_text"]
        ans = test["knowledge_base_answer"]
        weight = test["weight"]

        rfp_chunks = [topk["text"] for topk in test["rfp_topk"]]

        print(f"Calculating score for query {query_number}")
        res : ScoreResponse = _calculate_score(rfp_chunks, question, ans)
        all_scores[query_phase - 1].append(res)

        score = res.score
        final_scores[query_phase - 1].append(score * weight)
        

    # map list of tups to weighted average

    phase_1_total = sum(final_scores[0])
    phase_2_total = sum(final_scores[1])
    phase_3_total = sum(final_scores[2])
    phase_4_total = sum(final_scores[3])

    to_ret = {}
    to_ret["llm_eval"] = all_scores
    phase_1 = phase_1_total / len(final_scores[0])
    phase_2 = phase_2_total / len(final_scores[1])
    phase_3 = phase_3_total / len(final_scores[2])
    phase_4 = phase_4_total / len(final_scores[3])

    total = sum([phase_1_total, phase_2_total, phase_3_total, phase_4_total]) / sum([len(scores) for scores in final_scores])
    
    to_ret["scores"] = DisplayScores(
        phase_1=phase_1,
        phase_2=phase_2,
        phase_3=phase_3,
        phase_4=phase_4,
        total=total
    )
        
    return to_ret