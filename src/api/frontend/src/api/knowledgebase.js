/**
 * knowledgeBaseApi.js
 * Functions to interact with the backend knowledge base API
 */

export async function fetchQueries() {
  try {
    const response = await fetch("/knowledge_base/get_all_query_rows");
    const data = await response.json();
    return data?.data || [];
  } catch (error) {
    console.error("Error fetching queries:", error);
    return [];
  }
}

export async function createOrUpdateQuery(form, isEditing) {
  try {
    const endpoint = isEditing
      ? "/knowledge_base/update_query_row"
      : "/knowledge_base/create_query_row";

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
      `/knowledge_base/delete_query_row/${query_number}`,
      { method: "POST" }
    );
    return response.ok;
  } catch (error) {
    console.error("Error deleting:", error);
    return false;
  }
}
