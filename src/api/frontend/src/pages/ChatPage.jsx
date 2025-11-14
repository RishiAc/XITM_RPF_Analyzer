import React, { useState } from "react";
import { useParams, useLocation } from "react-router-dom";
import Navbar from "../components/Navbar";
import "./ChatPage.css";

const phaseBlueprint = [
  {
    id: "P1",
    label: "Phase 1",
    title: "Eligibility & Kickoff",
    summary: "Confirm registrations and teaming agreements before investing effort in the response.",
  },
  {
    id: "P2",
    label: "Phase 2",
    title: "Scope & Technical Fit",
    summary: "Review the statement of work and align requirements with internal capabilities.",
  },
  {
    id: "P3",
    label: "Phase 3",
    title: "Evaluation Alignment",
    summary: "Map win themes to evaluation factors and identify supporting past performance.",
  },
  {
    id: "P4",
    label: "Phase 4",
    title: "Pricing & Submission",
    summary: "Finalize pricing assumptions, confirm due dates, and prepare the submission package.",
  },
];

const ChatPage = () => {
    const { id } = useParams();
    const location = useLocation();
    const title = location.state?.title || `RFP ${id}`;

    const overallScore = 82;
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");
    const [selectedPhase, setSelectedPhase] = useState(null);
    const [showPhaseModal, setShowPhaseModal] = useState(false);

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
        setSelectedPhase(phase);
        setShowPhaseModal(true);
    };

    const closePhaseModal = () => {
        setShowPhaseModal(false);
        setSelectedPhase(null);
    };

    return (
        <div className="chat-page-light">
            <Navbar />
            
            <div className="chat-layout">
                {/* Sidebar with Phases */}
                <aside className="phases-sidebar">
                    <div className="sidebar-header">
                        <h3>{title}</h3>
                        <div className="overall-score-light">
                            <div className="score-circle-light">
                                <span className="score-number-light">{overallScore}</span>
                            </div>
                            <span className="score-label-light">Overall Score</span>
                        </div>
                    </div>
                    
                    <div className="phases-list">
                        <h4>Phases</h4>
                        {phaseBlueprint.map((phase) => (
                            <button
                                key={phase.id}
                                className="phase-button"
                                onClick={() => handlePhaseClick(phase)}
                            >
                                <span className="phase-id">{phase.id}</span>
                                <span className="phase-title">{phase.title}</span>
                            </button>
                        ))}
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
            </div>

            {/* Phase Modal/Popup */}
            {showPhaseModal && selectedPhase && (
                <div className="phase-modal-overlay" onClick={closePhaseModal}>
                    <div className="phase-modal" onClick={(e) => e.stopPropagation()}>
                        <div className="phase-modal-header">
                            <h2>{selectedPhase.label}: {selectedPhase.title}</h2>
                            <button className="close-button" onClick={closePhaseModal}>×</button>
                        </div>
                        <div className="phase-modal-content">
                            <p>{selectedPhase.summary}</p>
                            <div className="phase-details">
                                <h3>Key Focus Areas</h3>
                                <ul>
                                    <li>Review eligibility requirements</li>
                                    <li>Assess technical capabilities</li>
                                    <li>Identify compliance needs</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ChatPage;
