import React, { useState, useEffect, useRef } from "react";
import { useParams, useLocation } from "react-router-dom";
import Navbar from "../components/Navbar";
import MetricCircle from "../components/MetricCircle";
import { queryRFP } from "../api/query";
import MarkdownView from "../components/MarkdownView";
import Source from "../components/Source";
import "./ChatPage.css";

const phaseBlueprint = [
  {
    id: "P1",
    label: "Phase 1",
    title: "Eligibility & Kickoff",
    metrics: [
      { label: "Due Date Realism", value: 87, max: 100, color: "#3b82f6" },
      { label: "Eligibility Status", value: 92, max: 100, color: "#10b981" },
    ],
    bullets: [
      "Due date realism",
      "Eligibility and set-aside status",
      "High-level SOW alignment",
    ],
  },
  {
    id: "P2",
    label: "Phase 2",
    title: "Scope & Technical Fit",
    metrics: [
      { label: "SOW Alignment", value: 85, max: 100, color: "#3b82f6" },
      { label: "Submission Readiness", value: 78, max: 100, color: "#10b981" },
    ],
    bullets: [
      "Detailed SOW review",
      "Proposal submission instructions (volumes, past performance requirements, resumes, formatting)",
      "Mandatory certifications or clearances",
    ],
  },
  {
    id: "P3",
    label: "Phase 3",
    title: "Evaluation Alignment",
    metrics: [
      { label: "Evaluation Score", value: 79, max: 100, color: "#f59e0b" },
      { label: "Competitive Position", value: 82, max: 100, color: "#3b82f6" },
    ],
    bullets: [
      "Evaluation criteria",
      "Award basis (LPTA vs Best Value)",
      "Competitive intelligence (new vs recompete, incumbent research)",
    ],
  },
  {
    id: "P4",
    label: "Phase 4",
    title: "Pricing & Submission",
    metrics: [
      { label: "Timeline Readiness", value: 88, max: 100, color: "#10b981" },
      { label: "Pricing Alignment", value: 83, max: 100, color: "#3b82f6" },
    ],
    bullets: [
      "Key dates and events (questions due, conferences, site visits)",
      "Pricing model (FFP, T&M, Labor Hour)",
    ],
  },
];

const fulfilledRequirements = [
  { id: 1, text: "SAM.gov registration verified", status: "complete", category: "Compliance" },
  { id: 2, text: "SDVOSB certification confirmed", status: "complete", category: "Eligibility" },
  { id: 3, text: "Past performance references compiled", status: "complete", category: "Evaluation" },
  { id: 4, text: "Technical capability matrix completed", status: "in-progress", category: "Technical" },
  { id: 5, text: "Pricing workbook 60% complete", status: "in-progress", category: "Pricing" },
  { id: 6, text: "FAR clause compliance review", status: "pending", category: "Compliance" },
];

const ChatPage = () => {
  const { id } = useParams();
  const location = useLocation();
  const title = location.state?.title || `RFP ${id}`;

  const overallScore = 82;
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeSourceIndex, setActiveSourceIndex] = useState(null);
  const [expandedPhase, setExpandedPhase] = useState(null);
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userInput = input;
    console.log(`INPUT: ${userInput}`);
    console.log(`ID: ${id}`);

    setMessages((prev) => [...prev, { type: "user", text: userInput }]);
    setInput("");
    setLoading(true);

    try {
      // Call your RFP query endpoint
      const response = await queryRFP(userInput, id);

      console.log("RFP RESPONSE");
      console.log(response);

      if (response.error === undefined) {
        // Handle different possible response structures
        const answer = response.answer || response.text || response.message || JSON.stringify(response);
        const sources = response.sources || response.results || [];
        
        setMessages((prev) => [
          ...prev,
          { type: "bot", text: String(answer), sources: Array.isArray(sources) ? sources : [] },
        ]);
      } else {
        const errorText = typeof response.error === "string" 
          ? response.error 
          : response.error?.message || JSON.stringify(response.error);
        setMessages((prev) => [
          ...prev,
          { type: "bot", text: String(errorText), sources: [] },
        ]);
      }
    } catch (err) {
      console.error(err);
      setMessages((prev) => [
        ...prev,
        { type: "bot", text: "Something went wrong. Please try again." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleSources = (index) => {
    setActiveSourceIndex((prev) => (prev === index ? null : index));
  };

  const handleCloseSources = () => {
    setActiveSourceIndex(null);
  };

  const handlePhaseClick = (phase) => {
    if (expandedPhase?.id === phase.id) {
      setExpandedPhase(null);
    } else {
      setExpandedPhase(phase);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "complete": return "#10b981";
      case "in-progress": return "#f59e0b";
      case "pending": return "#6b7280";
      default: return "#6b7280";
    }
  };

  const activeSources =
    activeSourceIndex !== null
      ? messages[activeSourceIndex]?.sources ?? []
      : [];

  const isSourcesOpen = activeSources.length > 0;

  return (
    <div className="chat-page-light">
      <Navbar />
      
      <div className="chat-layout">
        {/* Left Sidebar with Score and Requirements */}
        <aside className="metrics-sidebar">
          <div className="sidebar-header">
            <h3 className="sidebar-title">{title}</h3>
            <div className="overall-score-light">
              <div className="score-circle-wrapper">
                <svg className="score-circle-svg" viewBox="0 0 100 100">
                  <defs>
                    <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stopColor="#3b82f6" />
                      <stop offset="100%" stopColor="#1d4ed8" />
                    </linearGradient>
                  </defs>
                  <circle
                    className="score-circle-bg"
                    cx="50"
                    cy="50"
                    r="45"
                    fill="none"
                    stroke="#e5e5e6"
                    strokeWidth="8"
                  />
                  <circle
                    className="score-circle-progress"
                    cx="50"
                    cy="50"
                    r="45"
                    fill="none"
                    stroke="url(#scoreGradient)"
                    strokeWidth="8"
                    strokeDasharray={2 * Math.PI * 45}
                    strokeDashoffset={2 * Math.PI * 45 * (1 - overallScore / 100)}
                    strokeLinecap="round"
                    transform="rotate(-90 50 50)"
                  />
                </svg>
                <div className="score-circle-content">
                  <span className="score-number-light">{overallScore}</span>
                  <span className="score-percent">%</span>
                </div>
              </div>
              <span className="score-label-light">Overall Readiness</span>
            </div>
          </div>
          
          <div className="requirements-section">
            <div className="section-header">
              <h4>Fulfilled Requirements</h4>
              <span className="requirements-count">
                {fulfilledRequirements.filter(r => r.status === "complete").length}/{fulfilledRequirements.length}
              </span>
            </div>
            <div className="requirements-list">
              {fulfilledRequirements.map((req) => (
                <div key={req.id} className="requirement-item">
                  <div className="requirement-status-indicator" style={{ backgroundColor: getStatusColor(req.status) }} />
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

        {/* Main Chat Area */}
        <main className="chat-main-area">
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

                {loading && (
                  <div className="chat-message-light bot">
                    Thinking...
                  </div>
                )}

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

            <div
              className="chat-sources-panel"
              aria-label="Sources panel"
              aria-hidden={!isSourcesOpen}
            >
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
        </main>

        {/* Right Sidebar with Phases */}
        <aside className="phases-panel">
          <h4 className="phases-panel-title">Capture Phases</h4>
          <div className="phases-grid">
            {phaseBlueprint.map((phase) => (
              <div
                key={phase.id}
                className={`phase-box ${expandedPhase?.id === phase.id ? "expanded" : ""}`}
                onClick={() => handlePhaseClick(phase)}
              >
                <div className="phase-box-header">
                  <span className="phase-id">{phase.id}</span>
                  <span className="phase-title">{phase.title}</span>
                </div>
                {expandedPhase?.id === phase.id && (
                  <div className="phase-box-content">
                    <div className="phase-metrics-grid">
                      {phase.metrics.map((metric, idx) => (
                        <MetricCircle
                          key={idx}
                          value={metric.value}
                          max={metric.max}
                          label={metric.label}
                          color={metric.color}
                        />
                      ))}
                    </div>
                    <div className="phase-details">
                      <ul>
                        {phase.bullets.map((bullet, idx) => (
                          <li key={idx}>{bullet}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </aside>
      </div>
    </div>
  );
};

export default ChatPage;
