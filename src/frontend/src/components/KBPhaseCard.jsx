import React, { useState } from "react";
import "./KBPhaseCard.css";

/**
 * KBPhaseCard Component
 * 
 * Editable phase card for Knowledge Base management.
 * Allows adding, editing, and deleting queries within a phase.
 * 
 * @param {string} id - Phase identifier (e.g., "P1", "P2")
 * @param {string} title - Phase title (e.g., "Eligibility & Kickoff")
 * @param {number} phase - Phase number (1-5)
 * @param {Array} queries - Array of query objects for this phase
 * @param {boolean} isExpanded - Whether the phase card is expanded
 * @param {function} onToggle - Callback when card header is clicked
 * @param {function} onAddQuery - Callback to add a new query
 * @param {function} onEditQuery - Callback to edit a query
 * @param {function} onDeleteQuery - Callback to delete a query
 */
const KBPhaseCard = ({
    id,
    title,
    phase,
    queries = [],
    isExpanded,
    onToggle,
    onAddQuery,
    onEditQuery,
    onDeleteQuery,
}) => {
    const [isAdding, setIsAdding] = useState(false);
    const [editingQueryNumber, setEditingQueryNumber] = useState(null);
    const [form, setForm] = useState({
        rfp_query_text: "",
        knowledge_base_answer: "",
        weight: "1.0",
    });

    const isCustomPhase = phase === 5;

    const resetForm = () => {
        setForm({
            rfp_query_text: "",
            knowledge_base_answer: "",
            weight: "1.0",
        });
    };

    const handleHeaderClick = (e) => {
        if (e.target.closest(".kb-query-actions") || 
            e.target.closest(".kb-add-form") || 
            e.target.closest(".kb-edit-form") ||
            e.target.closest(".kb-add-btn")) {
            return;
        }
        onToggle();
    };

    const handleAddClick = (e) => {
        e.stopPropagation();
        setIsAdding(true);
        setEditingQueryNumber(null);
        resetForm();
    };

    const handleCancelAdd = (e) => {
        e.stopPropagation();
        setIsAdding(false);
        resetForm();
    };

    const handleSubmitAdd = async (e) => {
        e.preventDefault();
        e.stopPropagation();
        
        const success = await onAddQuery({
            rfp_query_text: form.rfp_query_text,
            knowledge_base_answer: form.knowledge_base_answer,
            weight: parseFloat(form.weight),
            query_phase: phase,
        });
        
        if (success) {
            setIsAdding(false);
            resetForm();
        }
    };

    const handleEditClick = (e, query) => {
        e.stopPropagation();
        setEditingQueryNumber(query.query_number);
        setIsAdding(false);
        setForm({
            rfp_query_text: query.rfp_query_text,
            knowledge_base_answer: query.knowledge_base_answer,
            weight: String(query.weight),
        });
    };

    const handleCancelEdit = (e) => {
        e.stopPropagation();
        setEditingQueryNumber(null);
        resetForm();
    };

    const handleSubmitEdit = async (e, queryNumber) => {
        e.preventDefault();
        e.stopPropagation();
        
        const success = await onEditQuery({
            query_number: queryNumber,
            rfp_query_text: isCustomPhase ? form.rfp_query_text : undefined,
            knowledge_base_answer: form.knowledge_base_answer,
            weight: parseFloat(form.weight),
            query_phase: phase,
        });
        
        if (success) {
            setEditingQueryNumber(null);
            resetForm();
        }
    };

    const handleDeleteClick = (e, queryNumber) => {
        e.stopPropagation();
        onDeleteQuery(queryNumber, phase);
    };

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setForm((prev) => ({ ...prev, [name]: value }));
    };

    const handleFormClick = (e) => {
        e.stopPropagation();
    };

    return (
        <div
            className={`kb-phase-card ${isExpanded ? "expanded" : ""}`}
            onClick={handleHeaderClick}
        >
            <div className="kb-phase-card-header">
                <span className="kb-phase-card-id">{id}</span>
                <span className="kb-phase-card-title">{title}</span>
                <span className="kb-phase-card-count">
                    {queries.length} {queries.length === 1 ? "query" : "queries"}
                </span>
                <span className="kb-phase-card-expand-icon">
                    {isExpanded ? "▼" : "▶"}
                </span>
            </div>

            {isExpanded && (
                <div className="kb-phase-card-content" onClick={handleFormClick}>
                    {/* Add Query Button */}
                    {!isAdding && (
                        <button className="kb-add-btn" onClick={handleAddClick}>
                            + Add Query
                        </button>
                    )}

                    {/* Add Query Form */}
                    {isAdding && (
                        <form className="kb-add-form" onSubmit={handleSubmitAdd}>
                            <div className="kb-form-group">
                                <label>Query Text</label>
                                <textarea
                                    name="rfp_query_text"
                                    value={form.rfp_query_text}
                                    onChange={handleInputChange}
                                    placeholder="Enter the RFP query text..."
                                    required
                                    rows={2}
                                />
                            </div>
                            <div className="kb-form-group">
                                <label>Knowledge Base Answer</label>
                                <textarea
                                    name="knowledge_base_answer"
                                    value={form.knowledge_base_answer}
                                    onChange={handleInputChange}
                                    placeholder="Enter your company's answer..."
                                    required
                                    rows={3}
                                />
                            </div>
                            <div className="kb-form-group kb-form-row">
                                <div className="kb-weight-group">
                                    <label>Weight</label>
                                    <input
                                        type="number"
                                        name="weight"
                                        value={form.weight}
                                        onChange={handleInputChange}
                                        step="0.1"
                                        min="0"
                                        required
                                    />
                                </div>
                                <div className="kb-form-actions">
                                    <button type="submit" className="kb-save-btn">
                                        Add
                                    </button>
                                    <button
                                        type="button"
                                        className="kb-cancel-btn"
                                        onClick={handleCancelAdd}
                                    >
                                        Cancel
                                    </button>
                                </div>
                            </div>
                        </form>
                    )}

                    {/* Query List */}
                    {queries.length === 0 && !isAdding ? (
                        <div className="kb-phase-card-empty">
                            No queries in this phase yet. Click "Add Query" to create one.
                        </div>
                    ) : (
                        <div className="kb-query-list">
                            {queries.map((query) => (
                                <div key={query.query_number} className="kb-query-item">
                                    {editingQueryNumber === query.query_number ? (
                                        <form
                                            className="kb-edit-form"
                                            onSubmit={(e) => handleSubmitEdit(e, query.query_number)}
                                        >
                                            <div className="kb-form-group">
                                                <label>Query Text</label>
                                                <textarea
                                                    name="rfp_query_text"
                                                    value={form.rfp_query_text}
                                                    onChange={handleInputChange}
                                                    readOnly={!isCustomPhase}
                                                    className={!isCustomPhase ? "readonly" : ""}
                                                    rows={2}
                                                />
                                            </div>
                                            <div className="kb-form-group">
                                                <label>Knowledge Base Answer</label>
                                                <textarea
                                                    name="knowledge_base_answer"
                                                    value={form.knowledge_base_answer}
                                                    onChange={handleInputChange}
                                                    required
                                                    rows={3}
                                                />
                                            </div>
                                            <div className="kb-form-group kb-form-row">
                                                <div className="kb-weight-group">
                                                    <label>Weight</label>
                                                    <input
                                                        type="number"
                                                        name="weight"
                                                        value={form.weight}
                                                        onChange={handleInputChange}
                                                        step="0.1"
                                                        min="0"
                                                        required
                                                    />
                                                </div>
                                                <div className="kb-form-actions">
                                                    <button type="submit" className="kb-save-btn">
                                                        Save
                                                    </button>
                                                    <button
                                                        type="button"
                                                        className="kb-cancel-btn"
                                                        onClick={handleCancelEdit}
                                                    >
                                                        Cancel
                                                    </button>
                                                </div>
                                            </div>
                                        </form>
                                    ) : (
                                        <>
                                            <div className="kb-query-header">
                                                <span className="kb-query-number">
                                                    Q{query.query_number}
                                                </span>
                                                <span className="kb-query-weight">
                                                    Weight: {query.weight}
                                                </span>
                                            </div>
                                            <div className="kb-query-text">
                                                {query.rfp_query_text}
                                            </div>
                                            <div className="kb-query-answer">
                                                <span className="kb-answer-label">Answer:</span>
                                                {query.knowledge_base_answer}
                                            </div>
                                            {query.knowledge_base_chunks &&
                                                query.knowledge_base_chunks.length > 0 && (
                                                <div className="kb-query-evidence">
                                                    <span className="kb-evidence-label">
                                                        Company evidence ({query.knowledge_base_chunks.length} chunks):
                                                    </span>
                                                    {query.knowledge_base_chunks.map((chunk, idx) => (
                                                        <div key={idx} className="kb-evidence-chunk">
                                                            {typeof chunk === "object" && chunk.text
                                                                ? chunk.text.slice(0, 80).trim() +
                                                                  (chunk.text.length > 80 ? "…" : "")
                                                                : String(chunk).slice(0, 80) + "…"}
                                                        </div>
                                                    ))}
                                                </div>
                                            )}
                                            <div className="kb-query-actions">
                                                <button
                                                    className="kb-edit-btn"
                                                    onClick={(e) => handleEditClick(e, query)}
                                                >
                                                    Edit
                                                </button>
                                                {isCustomPhase && (
                                                    <button
                                                        className="kb-delete-btn"
                                                        onClick={(e) =>
                                                            handleDeleteClick(e, query.query_number)
                                                        }
                                                    >
                                                        Delete
                                                    </button>
                                                )}
                                            </div>
                                        </>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default KBPhaseCard;
