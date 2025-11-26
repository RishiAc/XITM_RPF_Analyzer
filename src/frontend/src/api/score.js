/**
 * Calls scoring api to get scores from the given rfp for all phases
 * @param {string} rfpDocID the qdrant doc_id of the rfp being queried
 * @returns {object} an object containing the scores for each phase, and each individual query score/reasoning
 */
export async function getPhaseScores(rfpDocID) {
    try {
        // Prepare payload to call scoring api
        const payload = {
            rfp_id: "", // Placeholder until this is removed from OchestratorBody
            rfp_doc_id: rfpDocID
        };
        
        // Call scoring api
        const response = await fetch("http://localhost:8080/score/score-rfp", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errText = await response.text();
            throw new Error(`Scoring failed: ${response.status} ${errText}`);
        }

        return await response.json()
    }
    catch (err) {
        console.error("Error getting phase scores: ", err);
        throw err;
    }
}