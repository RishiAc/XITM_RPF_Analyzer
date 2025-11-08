import React, { useState, useEffect, useRef } from "react";
import { useParams, useLocation } from "react-router-dom";
import Navbar from "../components/Navbar";
import "./ChatPage.css";
import { queryRFP } from "../api/query";
import MarkdownView from "../components/MarkdownView";
import Source from "../components/Source";

const ChatPage = () => {
  const { id } = useParams();
  const location = useLocation();
  const title = location.state?.title || `RFP ${id}`;

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeSourceIndex, setActiveSourceIndex] = useState(null);
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
        setMessages((prev) => [
          ...prev,
          { type: "bot", text: response.answer, sources: response.sources },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          { type: "bot", text: response.error, sources: [] },
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

  const activeSources =
    activeSourceIndex !== null
      ? messages[activeSourceIndex]?.sources ?? []
      : [];

  const isSourcesOpen = activeSources.length > 0;

  return (
    <div className="chat-page">
      <Navbar />

      <div className="chat-title">
        <h2>{title}</h2>
      </div>

      <div
        className={`chat-container${isSourcesOpen ? " sources-open" : ""}`}
      >
        <section className="chat-main">
          <div className="chat-box">
          {messages.map((msg, idx) => (
            <div key={idx} className={`chat-message ${msg.type}`}>
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
            <div className="chat-message bot">
              Thinking...
            </div>
          )}

          <div ref={chatEndRef} />
          </div>

          <div className="chat-input-container">
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
    </div>
  );
};

export default ChatPage;
