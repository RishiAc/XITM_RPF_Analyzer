import { useEffect, useState } from "react";
import Navbar from "../components/Navbar";
import "./KnowledgeBasePage.css";
import {
    fetchQueries as fetchQueriesApi,
    createOrUpdateQuery,
    deleteQuery as deleteQueryApi,
} from "../api/knowledgebase";

const KnowledgeBasePage = () => {
    const [queries, setQueries] = useState([]);
    const [form, setForm] = useState({
        query_number: "",
        knowledge_base_answer: "",
        rfp_query_text: "",
        weight: "",
    });
    const [isEditing, setIsEditing] = useState(false);

    const fetchQueries = async () => {
        const data = await fetchQueriesApi();
        setQueries(data);
    };

    useEffect(() => {
        fetchQueries();
    }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();

        const payload = {
            ...form,
            weight: Number(form.weight),
            query_phase: 5, // always phase 5
            query_number: isEditing
                ? Number(form.query_number)
                : Math.max(0, ...queries.map((q) => q.query_number)) + 1,
        };

        const success = await createOrUpdateQuery(payload, isEditing);
        if (success) {
            setForm({
                query_number: "",
                knowledge_base_answer: "",
                rfp_query_text: "",
                weight: "",
            });
            setIsEditing(false);
            fetchQueries();
        }
    };

    const handleDelete = async (query_number, query_phase) => {
        if (query_phase < 5) return;
        const success = await deleteQueryApi(query_number);
        if (success) fetchQueries();
    };

    const handleEdit = (q) => {
        if (q.query_phase < 5) return;
        setForm({ ...q });
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
                    {/* Table Section */}
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
                                            {q.query_phase === 5 && (
                                                <>
                                                    <button
                                                        className="edit-btn"
                                                        onClick={() => handleEdit(q)}
                                                    >
                                                        Edit
                                                    </button>
                                                    <button
                                                        className="delete-btn"
                                                        onClick={() => handleDelete(q.query_number, q.query_phase)}
                                                    >
                                                        Delete
                                                    </button>
                                                </>
                                            )}
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

                    {/* Form Section */}
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
