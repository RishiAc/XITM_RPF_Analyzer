/**
 * Evaluate a firm's QA answer against RFP text using FastAPI endpoint
 * @param {string} docId - RFP document ID
 * @param {string} query - User's query or prompt
 * @param {string} qaAnswer - Firm's QA answer (user input)
 * @param {number} [topK=5] - Number of top results to consider
 * @returns {Promise<{score: number, explanation: string}>}
 */
export async function evaluateLLM(docId, query, qaAnswer, topK = 5) {
  try {
    const body = {
      doc_id: String(docId),
      query,
      qa_answer: qaAnswer,
      top_k: topK,
    };

    const response = await fetch("http://localhost:8080/eval/llm-eval", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Evaluation failed: ${response.status} ${errorText}`);
    }

    const result = await response.json();
    return result;
  } catch (err) {
    console.error("Error calling /eval/llm-eval:", err);
    throw err;
  }
}