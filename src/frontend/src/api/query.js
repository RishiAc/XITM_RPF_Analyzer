/**
 * 
 * @param {string} query 
 * @param {string} rfp_doc_id
 */

export async function queryRFP(query, rfp_doc_id) {

    const URL = "http://localhost:8000/query/query-rfp"

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

        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        return res.json()
    }
    catch (err) {
        return {
            "error": err
        }
    }
}