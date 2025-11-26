import { useState } from "react";
import { useParams, useLocation } from "react-router-dom";
import { getPhaseScores } from "../api/score";
import { getColor } from "../api/colors";
import Navbar from "../components/Navbar";
import MetricCircle from "../components/MetricCircle";
import "./ChatPage.css";

const url = window.location.href
const scores = getPhaseScores(url.substring(url.lastIndexOf("/") + 1));

const phaseBlueprint = [
  {
    id: "P1",
    label: "Phase 1",
    title: "Eligibility & Kickoff",
    metrics: scores.llm_eval[0].map((query) => {
        return {label: query.reasoning, value: query.score, max: 5, color: getColor(query.score)};
    }),
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
    metrics: scores.llm_eval[1].map((query) => {
        return {label: query.reasoning, value: query.score, max: 5, color: getColor(query.score)};
    }),
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
    metrics: scores.llm_eval[2].map((query) => {
        return {label: query.reasoning, value: query.score, max: 5, color: getColor(query.score)};
    }),
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
    metrics: scores.llm_eval[3].map((query) => {
        return {label: query.reasoning, value: query.score, max: 5, color: getColor(query.score)};
    }),
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
    const [expandedPhase, setExpandedPhase] = useState(null);

    const sendMessage = () => {
        if (!input.trim()) return;
        setMessages((prev) => [
            ...prev,
            { type: "user", text: input },
            { type: "bot", text: "This is a filler response." },
        ]);
        setInput("");
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
                    <div className="chat-container-light">
                        <div className="chat-box-light">
                            {messages.length === 0 && (
                                <div className="chat-welcome-light">
                                    <h1>How can I help you with {title}?</h1>
                                    <p>Ask questions about this RFP or get insights.</p>
                                </div>
                            )}
                            {messages.map((msg, idx) => (
                                <div
                                    key={idx}
                                    className={`chat-message-light ${msg.type}`}
                                >
                                    {msg.type === "bot"
                                        ? `Most Relevant Chunk: ${msg.text}`
                                        : msg.text}
                                </div>
                            ))}
                        </div>
                        <div className="chat-input-container-light">
                            <input
                                type="text"
                                placeholder="Type a message..."
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                            />
                            <button onClick={sendMessage}>Send</button>
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
