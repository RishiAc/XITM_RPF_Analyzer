import React from "react";
import MetricCircle from "./MetricCircle";
import "./PhaseCard.css";

/**
 * PhaseCard Component
 * 
 * Displays a capture phase with query/answer pairs from orchestrate-eval API
 * 
 * @param {string} id - Phase identifier (e.g., "P1", "P2")
 * @param {string} title - Phase title (e.g., "Eligibility & Kickoff")
 * @param {number} score - Phase score (1-5 scale)
 * @param {Array} queries - Array of query objects from orchestrate-eval API
 * @param {boolean} isExpanded - Whether the phase card is expanded
 * @param {function} onToggle - Callback when card is clicked to toggle expansion
 */
const PhaseCard = ({ id, title, score, queries = [], isExpanded, onToggle }) => {
    
    /**
     * Get color class based on score (1-5 scale)
     */
    const getScoreColor = (scoreVal) => {
        if (scoreVal >= 4) return "score-high";
        if (scoreVal >= 3) return "score-medium";
        return "score-low";
    };

    /**
     * Get color hex based on score (1-5 scale)
     */
    const getScoreColorHex = (scoreVal) => {
        if (scoreVal >= 4) return "#10b981"; // green
        if (scoreVal >= 3) return "#f59e0b"; // yellow
        return "#ef4444"; // red
    };

    /**
     * Get score label text
     */
    const getScoreLabel = (scoreVal) => {
        switch (scoreVal) {
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
                
                {/* Show MetricCircle if score is available, otherwise show query count */}
                {score !== undefined && score !== null ? (
                    <div className="phase-card-score">
                        <MetricCircle
                            value={Number(score.toFixed(1))}
                            max={5}
                            label=""
                            color={getScoreColorHex(score)}
                        />
                    </div>
                ) : (
                    <span className="phase-card-count">
                        {queries.length} {queries.length === 1 ? "query" : "queries"}
                    </span>
                )}
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
                                    {/* Top: Q tag, question/query, score tag */}
                                    <div className="phase-query-header">
                                        <span className="phase-query-number">
                                            Q{query.query_number || idx + 1}
                                        </span>
                                        <h4 className="phase-query-text">
                                            {query.rfp_query_text}
                                        </h4>
                                        {query.evaluation && (
                                            <span className={`phase-query-score ${getScoreColor(query.evaluation.score)}`}>
                                                {query.evaluation.score}/5 · {getScoreLabel(query.evaluation.score)}
                                            </span>
                                        )}
                                    </div>

                                    {/* Middle: Analysis (evaluation) or summary fallback */}
                                    {(query.evaluation?.explanation || query.generated_summary) && (
                                        <div className="phase-query-answer">
                                            <span className="answer-label">
                                                {query.evaluation?.explanation ? "ANALYSIS:" : "SUMMARY:"}
                                            </span>
                                            {query.evaluation?.explanation || query.generated_summary}
                                        </div>
                                    )}

                                    {/* Bottom: Knowledge Base (manual answer) - if exists */}
                                    {query.knowledge_base_answer && (
                                        <div className="phase-query-kb">
                                            <span className="kb-label">KNOWLEDGE BASE:</span>
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
