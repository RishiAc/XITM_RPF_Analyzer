/**
 * 
 * @param {string} query 
 * @param {string} rfp_doc_id
 */

import { client } from "./client";

export async function queryRFP(query, rfp_doc_id) {

<<<<<<< HEAD
    const URL = `${client.stagingBackendUrl}/query/query-rfp`
=======
    const URL = "http://localhost:8080/query/query-rfp"
>>>>>>> 7eef9fe9320946e31e7c569b68eb48cee06258b9

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