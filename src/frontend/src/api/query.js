const BASE_URL = "http://localhost:8080";  // backend origin

/**
 * Fetch all knowledge base queries
 */
export async function fetchQueries() {
    try {
        const response = await fetch(
            `${BASE_URL}/knowledge_base/get_all_query_rows`
        );

        const data = await response.json();
        console.log(data);
        return data?.data || [];
    } catch (error) {
        console.error("Error fetching queries:", error);
        return [];
    }
}

export async function createOrUpdateQuery(form, isEditing) {
    try {
        const endpoint = isEditing
            ? `${BASE_URL}/knowledge_base/update_query_row`
            : `${BASE_URL}/knowledge_base/create_query_row`;

        const payload = {
            ...form,
            weight: parseFloat(form.weight),
            query_phase: parseInt(form.query_phase),
        };

        const response = await fetch(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        return response.ok;
    } catch (error) {
        console.error("Error submitting form:", error);
        return false;
    }
}

export async function deleteQuery(query_number) {
    if (!window.confirm("Delete this query?")) return false;

    try {
        const response = await fetch(
            `${BASE_URL}/knowledge_base/delete_query_row/${query_number}`,
            { method: "POST" }
        );
        return response.ok;
    } catch (error) {
        console.error("Error deleting:", error);
        return false;
    }
}

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

/**
 * 
 * @param {string} query 
 * @param {string} rfp_doc_id
 */

export async function queryRFP(query, rfp_doc_id) {

    const URL = "http://localhost:8080/query/query-rfp"

    if (!query) throw new Error("No Query Provided");

    try {
        // build payload

        const payload = {
            "query": query,
            "rfp_doc_id": rfp_doc_id
        }
        
        // make request 

        const res = await fetch(URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        })

        if (!res.ok) {
            // Try to surface backend error detail instead of a generic HTTP code
            let errorDetail = `HTTP ${res.status}`;
            try {
                const data = await res.json();
                if (data?.detail) {
                    errorDetail = data.detail;
                } else if (data?.error) {
                    errorDetail = data.error;
                }
            } catch {
                const text = await res.text();
                if (text) errorDetail = text;
            }
            return { error: errorDetail };
        }

        return res.json()
    }
    catch (err) {
        return {
            "error": err
        }
    }
}
