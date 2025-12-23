import React from "react";
import "./PhaseCard.css";

/**
 * PhaseCard Component
 * 
 * Displays a capture phase with query/answer pairs from orchestrate-eval API
 * 
 * @param {string} id - Phase identifier (e.g., "P1", "P2")
 * @param {string} title - Phase title (e.g., "Eligibility & Kickoff")
 * @param {Array} queries - Array of query objects from orchestrate-eval API
 * @param {boolean} isExpanded - Whether the phase card is expanded
 * @param {function} onToggle - Callback when card is clicked to toggle expansion
 */
const PhaseCard = ({ id, title, queries = [], isExpanded, onToggle }) => {
    
    /**
     * Get color class based on score (1-5 scale)
     */
    const getScoreColor = (score) => {
        if (score >= 4) return "score-high";
        if (score >= 3) return "score-medium";
        return "score-low";
    };

    /**
     * Get score label text
     */
    const getScoreLabel = (score) => {
        switch (score) {
            case 5: return "Excellent";
            case 4: return "Strong";
            case 3: return "Moderate";
            case 2: return "Weak";
            case 1: return "Poor";
            default: return "N/A";
        }
    };

    return (
        <div
            className={`phase-card ${isExpanded ? "expanded" : ""}`}
            onClick={onToggle}
        >
            <div className="phase-card-header">
                <span className="phase-card-id">{id}</span>
                <span className="phase-card-title">{title}</span>
                <span className="phase-card-count">
                    {queries.length} {queries.length === 1 ? "query" : "queries"}
                </span>
            </div>

            {isExpanded && (
                <div className="phase-card-content">
                    {queries.length === 0 ? (
                        <div className="phase-card-empty">
                            No queries evaluated for this phase yet.
                        </div>
                    ) : (
                        <div className="phase-query-list">
                            {queries.map((query, idx) => (
                                <div key={query.query_number || idx} className="phase-query-item">
                                    <div className="phase-query-header">
                                        <span className="phase-query-number">
                                            Q{query.query_number || idx + 1}
                                        </span>
                                        {query.evaluation && (
                                            <span className={`phase-query-score ${getScoreColor(query.evaluation.score)}`}>
                                                {query.evaluation.score}/5 · {getScoreLabel(query.evaluation.score)}
                                            </span>
                                        )}
                                        {query.generated_summary && (
                                            <div className="phase-query-answer">
                                                <span className="answer-label">Summary:</span>
                                                {query.generated_summary}
                                            </div>
                                            )}
                                    </div>
                                    
                                    <div className="phase-query-text">
                                        {query.rfp_query_text}
                                    </div>
                                    
                                    {query.evaluation?.explanation && (
                                        <div className="phase-query-answer">
                                            <span className="answer-label">Analysis:</span>
                                            {query.evaluation.explanation}
                                        </div>
                                    )}

                                    {query.knowledge_base_answer && (
                                        <div className="phase-query-kb">
                                            <span className="kb-label">Knowledge Base:</span>
                                            {query.knowledge_base_answer}
                                        </div>
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

export default PhaseCard;

