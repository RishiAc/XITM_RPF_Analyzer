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
