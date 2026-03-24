import React, { useState, useEffect, useRef } from "react";
import { useParams, useLocation } from "react-router-dom";
import Navbar from "../components/Navbar";
import PhaseCard from "../components/PhaseCard";
import MetricCircle from "../components/MetricCircle";
import { queryRFP } from "../api/query";
import { client } from "../api/client";
import MarkdownView from "../components/MarkdownView";
import Source from "../components/Source";
import "./ChatPage.css";

// Phase configuration - metadata for each capture phase
const PHASE_CONFIG = [
  { id: "P1", title: "Eligibility & Kickoff" },
  { id: "P2", title: "Scope & Technical Fit" },
  { id: "P3", title: "Evaluation Alignment" },
  { id: "P4", title: "Pricing & Submission" },
];

// Static requirements data (can be made dynamic later)
const fulfilledRequirements = [
  { id: 1, text: "SAM.gov registration verified", status: "complete", category: "Compliance" },
  { id: 2, text: "SDVOSB certification confirmed", status: "complete", category: "Eligibility" },
  { id: 3, text: "Past performance references compiled", status: "complete", category: "Evaluation" },
  { id: 4, text: "Technical capability matrix completed", status: "in-progress", category: "Technical" },
  { id: 5, text: "Pricing workbook 60% complete", status: "in-progress", category: "Pricing" },
  { id: 6, text: "FAR clause compliance review", status: "pending", category: "Compliance" },
];

/**
 * Group queries by their phase
 * @param {Array} queries - Array of query objects from orchestrate-eval API
 * @returns {Object} - Object with phase IDs as keys and arrays of queries as values
 */
const groupByPhase = (queries) => {
  return (queries || []).reduce((acc, query) => {
    const phaseKey = `P${query.query_phase ?? 1}`;
    if (!acc[phaseKey]) acc[phaseKey] = [];
    acc[phaseKey].push(query);
    return acc;
  }, {});
};

/**
 * Get color based on score (1-5 scale)
 */
const getScoreColor = (score) => {
  if (score >= 4) return "#10b981"; // green
  if (score >= 3) return "#f59e0b"; // yellow
  return "#ef4444"; // red
};

const API_BASE_URL = client.apiBaseUrl;

const ChatPage = () => {
  const { id } = useParams();
  const location = useLocation();
  const title = location.state?.title || `RFP ${id}`;

  const [overallScore, setOverallScore] = useState(null);
  const [phaseScores, setPhaseScores] = useState({});

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [expandedPhase, setExpandedPhase] = useState(null);
  const [phaseData, setPhaseData] = useState({});
  const [isLoading, setIsLoading] = useState(false);

  const [loading, setLoading] = useState(false);
  const [activeSourceIndex, setActiveSourceIndex] = useState(null);
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Load existing evaluations on mount
  useEffect(() => {
    const loadExistingEvals = async () => {
      if (!id) return;
      
      try {
        const response = await fetch(`${API_BASE_URL}/eval/get-evals?rfp_id=${id}`);
        
        if (!response.ok) {
          console.error("Failed to fetch existing evals");
          return;
        }
        
        const data = await response.json();
        
        // If evaluations exist, populate the state
        if (data.queries && data.queries.length > 0) {
          const grouped = groupByPhase(data.queries);
          setPhaseData(grouped);
          
          // Set scores if available
          if (data.scores) {
            setOverallScore(data.scores.total);
            setPhaseScores({
              P1: data.scores.phase1,
              P2: data.scores.phase2,
              P3: data.scores.phase3,
              P4: data.scores.phase4,
            });
          }
        }
      } catch (error) {
        console.error("Error loading existing evals:", error);
      }
    };
    
    loadExistingEvals();
  }, [id]);

  // Fetch scores from the scoring API
  const fetchScores = async () => {
    try {
      const scoreRes = await fetch(`${API_BASE_URL}/score/score-rfp?rfp_id=${id}`, {
        method: "POST",
      });
      
      if (!scoreRes.ok) {
        console.error("Failed to fetch scores");
        return;
      }
      
      const scores = await scoreRes.json();
      
      // Store scores on 1-5 scale
      setOverallScore(scores.total);
      setPhaseScores({
        P1: scores.phase1,
        P2: scores.phase2,
        P3: scores.phase3,
        P4: scores.phase4,
      });
    } catch (error) {
      console.error("Error fetching scores:", error);
    }
  };

  // Fetch evaluation data from batch-orchestrate-eval API (button-triggered)
  const fetchEvaluationData = async () => {
    if (!id) return;

    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/eval/batch-orchestrate-eval`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          rfp_id: id,
          rfp_doc_id: id,
          top_k: 5,
          batch_size: 3
        }),
      });

      if (!response.ok) throw new Error("Failed to fetch evaluation data");

      const data = await response.json();

      if (data.queries) {
        const grouped = groupByPhase(data.queries);
        setPhaseData(grouped);
        
        // After evaluation completes, fetch and update scores
        await fetchScores();
      } else {
        setPhaseData({});
      }
    } catch (error) {
      console.error("Error fetching evaluation data:", error);
      setPhaseData({});
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userInput = input;

    console.log(`INPUT: ${userInput}`);
    console.log(`ID: ${id}`);

    setMessages((prev) => [...prev, { type: "user", text: userInput }]);
    setInput("");
    setLoading(true);

    try {
      const response = await queryRFP(userInput, id);

      console.log("RFP RESPONSE");
      console.log(response);

      if (response?.error === undefined) {
        const answer =
          response?.answer ?? response?.text ?? response?.message ?? JSON.stringify(response);
        const sources = response?.sources ?? response?.results ?? [];

        setMessages((prev) => [
          ...prev,
          { type: "bot", text: String(answer), sources: Array.isArray(sources) ? sources : [] },
        ]);
      } else {
        const errorText =
          typeof response.error === "string"
            ? response.error
            : response.error?.message || JSON.stringify(response.error);

        setMessages((prev) => [...prev, { type: "bot", text: String(errorText), sources: [] }]);
      }
    } catch (err) {
      console.error(err);
      setMessages((prev) => [
        ...prev,
        { type: "bot", text: "Something went wrong. Please try again.", sources: [] },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleSources = (index) => {
    setActiveSourceIndex((prev) => (prev === index ? null : index));
  };

  const handleCloseSources = () => setActiveSourceIndex(null);

  const activeSources =
    activeSourceIndex !== null ? messages[activeSourceIndex]?.sources ?? [] : [];

  const isSourcesOpen = activeSources.length > 0;

  const handlePhaseClick = (phaseId) => {
    setExpandedPhase((prev) => (prev === phaseId ? null : phaseId));
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "complete":
        return "#10b981";
      case "in-progress":
        return "#f59e0b";
      case "pending":
      default:
        return "#6b7280";
    }
  };

  return (
    <div className="chat-page-light">
      <Navbar />

      <div className="chat-layout">
        {/* Left Sidebar with Score and Requirements */}
        <aside className="metrics-sidebar">
          <div className="sidebar-header">
            <h3 className="sidebar-title">{title}</h3>
            <div className="overall-score-light">
              {overallScore !== null ? (
                <MetricCircle
                  value={Number(overallScore.toFixed(1))}
                  max={5}
                  label="Overall Readiness"
                  color={getScoreColor(overallScore)}
                />
              ) : (
                <MetricCircle
                  value={0}
                  max={5}
                  label="Overall Readiness"
                  color="#6b7280"
                />
              )}
            </div>
          </div>

          <div className="requirements-section">
            <div className="section-header">
              <h4>Fulfilled Requirements</h4>
              <span className="requirements-count">
                {fulfilledRequirements.filter((r) => r.status === "complete").length}/
                {fulfilledRequirements.length}
              </span>
            </div>

            <div className="requirements-list">
              {fulfilledRequirements.map((req) => (
                <div key={req.id} className="requirement-item">
                  <div
                    className="requirement-status-indicator"
                    style={{ backgroundColor: getStatusColor(req.status) }}
                  />
                  <div className="requirement-content">
                    <span className="requirement-text">{req.text}</span>
                    <span className="requirement-category">{req.category}</span>
                  </div>
                  <div className={`requirement-badge requirement-badge-${req.status}`}>
                    {req.status === "complete" ? "✓" : req.status === "in-progress" ? "⟳" : "○"}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </aside>

        {/* Middle Section - Phases */}
        <section className="phases-panel-center">
          <div className="phases-panel-header">
            <h4 className="phases-panel-title">Capture Phases</h4>
            <button
              className="run-analysis-btn"
              onClick={fetchEvaluationData}
              disabled={isLoading}
            >
              {isLoading ? "Analyzing..." : "Run Analysis"}
            </button>
          </div>

          <div className="phases-grid">
            {PHASE_CONFIG.map((phase) => (
              <PhaseCard
                key={phase.id}
                id={phase.id}
                title={phase.title}
                score={phaseScores[phase.id]}
                queries={phaseData[phase.id] || []}
                isExpanded={expandedPhase === phase.id}
                onToggle={() => handlePhaseClick(phase.id)}
              />
            ))}
          </div>
        </section>

        {/* Right Sidebar - Chat */}
        <aside className="chat-sidebar-right">
          <div className="chat-title-light">
            <h2>{title}</h2>
          </div>

          <div className={`chat-container-light${isSourcesOpen ? " sources-open" : ""}`}>
            <section className="chat-main">
              <div className="chat-box-light">
                {messages.length === 0 && (
                  <div className="chat-welcome-light">
                    <h1>How can I help you with {title}?</h1>
                    <p>Ask questions about this RFP or get insights.</p>
                  </div>
                )}

                {messages.map((msg, idx) => (
                  <div key={idx} className={`chat-message-light ${msg.type}`}>
                    {msg.type === "bot" ? (
                      <>
                        <MarkdownView md={msg.text} />
                        {msg.sources?.length ? (
                          <button
                            type="button"
                            className="chat-message__sources-button"
                            onClick={() => handleToggleSources(idx)}
                          >
                            Sources ({msg.sources.length})
                          </button>
                        ) : null}
                      </>
                    ) : (
                      msg.text
                    )}
                  </div>
                ))}

                {loading && <div className="chat-message-light bot">Thinking...</div>}

                <div ref={chatEndRef} />
              </div>

              <div className="chat-input-container-light">
                <input
                  type="text"
                  placeholder="Type a message..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                  disabled={loading}
                />
                <button onClick={sendMessage} disabled={loading}>
                  {loading ? "Sending..." : "Send"}
                </button>
              </div>
            </section>

            <div className="chat-sources-panel" aria-label="Sources panel" aria-hidden={!isSourcesOpen}>
              {isSourcesOpen ? (
                <>
                  <div className="chat-sources-panel__header">
                    <h3>Sources</h3>
                    <button
                      type="button"
                      className="chat-sources-panel__close"
                      onClick={handleCloseSources}
                    >
                      ×
                    </button>
                  </div>
                  <div className="chat-sources-panel__body">
                    {activeSources.map((source, index) => (
                      <Source key={index} text={source} />
                    ))}
                  </div>
                </>
              ) : null}
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
};

export default ChatPage;
