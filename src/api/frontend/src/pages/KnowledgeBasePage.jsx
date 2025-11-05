import React, { useEffect, useState } from "react";
import Navbar from "../components/Navbar";
import "./KnowledgeBasePage.css";

const KnowledgeBasePage = () => {
  const [queries, setQueries] = useState([]);
  const [form, setForm] = useState({
    query_number: "",
    knowledge_base_answer: "",
    rfp_query_text: "",
    weight: "",
    query_phase: "",
  });
  const [isEditing, setIsEditing] = useState(false);

  // Fetch all queries
  const fetchQueries = async () => {
    try {
      const response = await fetch("/knowledge_base/get_all_query_rows");
      const data = await response.json();
      if (data && data.data) setQueries(data.data);
    } catch (error) {
      console.error("Error fetching queries:", error);
    }
  };

  useEffect(() => {
    fetchQueries();
  }, []);

  // Handle add or update
  const handleSubmit = async (e) => {
    e.preventDefault();
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

      if (response.ok) {
        setForm({
          query_number: "",
          knowledge_base_answer: "",
          rfp_query_text: "",
          weight: "",
          query_phase: "",
        });
        setIsEditing(false);
        fetchQueries();
      }
    } catch (error) {
      console.error("Error submitting form:", error);
    }
  };

  // Handle delete
  const handleDelete = async (query_number) => {
    if (!window.confirm("Delete this query?")) return;
    try {
      const response = await fetch(
        `/knowledge_base/delete_query_row/${query_number}`,
        { method: "POST" }
      );
      if (response.ok) fetchQueries();
    } catch (error) {
      console.error("Error deleting:", error);
    }
  };

  const handleEdit = (q) => {
    setForm(q);
    setIsEditing(true);
  };

  return (
    <div className="kb-container">
      <Navbar />

      <div className="kb-page-content">
        <header className="kb-header">
          <h1>
            Knowledge <span>Base</span>
          </h1>
          <p>Manage your stored RFP queries and knowledge base answers.</p>
        </header>

        <main className="kb-content">
          <section className="kb-table-section">
            <table className="kb-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Answer</th>
                  <th>Query Text</th>
                  <th>Weight</th>
                  <th>Phase</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {queries.map((q) => (
                  <tr key={q.query_number}>
                    <td>{q.query_number}</td>
                    <td>{q.knowledge_base_answer}</td>
                    <td>{q.rfp_query_text}</td>
                    <td>{q.weight}</td>
                    <td>{q.query_phase}</td>
                    <td>
                      <button className="edit-btn" onClick={() => handleEdit(q)}>
                        Edit
                      </button>
                      <button
                        className="delete-btn"
                        onClick={() => handleDelete(q.query_number)}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
                {queries.length === 0 && (
                  <tr>
                    <td colSpan="6" style={{ textAlign: "center", color: "#555" }}>
                      No queries found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </section>

          <section className="kb-form-section">
            <div className="kb-form-card">
              <h2>{isEditing ? "Update Query" : "Add Query"}</h2>
              <form onSubmit={handleSubmit}>
                {isEditing && (
                  <input
                    type="number"
                    value={form.query_number}
                    readOnly
                    className="readonly"
                  />
                )}
                <input
                  type="text"
                  placeholder="RFP Query Text"
                  value={form.rfp_query_text}
                  onChange={(e) =>
                    setForm({ ...form, rfp_query_text: e.target.value })
                  }
                  required
                />
                <input
                  type="text"
                  placeholder="Knowledge Base Answer"
                  value={form.knowledge_base_answer}
                  onChange={(e) =>
                    setForm({ ...form, knowledge_base_answer: e.target.value })
                  }
                  required
                />
                <input
                  type="number"
                  step="0.1"
                  placeholder="Weight"
                  value={form.weight}
                  onChange={(e) => setForm({ ...form, weight: e.target.value })}
                  required
                />
                <input
                  type="number"
                  placeholder="Query Phase"
                  value={form.query_phase}
                  onChange={(e) =>
                    setForm({ ...form, query_phase: e.target.value })
                  }
                  required
                />

                <button type="submit" className="submit-btn">
                  {isEditing ? "Update" : "Add"}
                </button>
              </form>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
};

export default KnowledgeBasePage;
