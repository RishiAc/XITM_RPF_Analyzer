/**
 * 
 * @param {string} query 
 * @param {string} rfp_doc_id
 */
export async function queryRFP(query, rfp_doc_id) {

    const URL = "http://localhost:8080/query/query-rfp";

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
