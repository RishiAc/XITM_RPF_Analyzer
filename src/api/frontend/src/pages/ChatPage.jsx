import React, { useState, useEffect, useRef } from "react";
import { useParams, useLocation } from "react-router-dom";
import Navbar from "../components/Navbar";
import { evaluateLLM } from "../api/evaluateLLM";
import "./ChatPage.css";

const ChatPage = () => {
  const { id } = useParams();
  const location = useLocation();
  const title = location.state?.title || `RFP ${id}`;

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = { type: "user", text: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      // 🔹 Call FastAPI endpoint
      const response = await evaluateLLM(id, input, input, 5);

      const botMessage = {
        type: "bot",
        text: `Score: ${response.score ?? "N/A"}/5\nReasoning: ${response.explanation}`,
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (err) {
      const errorMessage = {
        type: "bot",
        text: `Error: ${err.message}`,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-page">
      <Navbar />
      <div className="chat-title">
        <h2>{title}</h2>
      </div>

      <div className="chat-container">
        <div className="chat-box">
          {messages.map((msg, idx) => (
            <div key={idx} className={`chat-message ${msg.type}`}>
              {msg.text.split("\n").map((line, i) => (
                <p key={i}>{line}</p>
              ))}
            </div>
          ))}
          {loading && <div className="chat-message bot">Thinking...</div>}
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
      </div>
    </div>
  );
};

export default ChatPage;
