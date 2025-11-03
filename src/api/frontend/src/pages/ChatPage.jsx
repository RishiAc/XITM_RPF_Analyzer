import React, { useState, useEffect, useRef } from "react";
import { useParams, useLocation } from "react-router-dom";
import Navbar from "../components/Navbar";
import { evaluateLLM } from "../api/evaluateLLM";
import "./ChatPage.css";
import { queryRFP } from "../api/query";
import MarkdownView from "../components/MarkdownView";

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

    const sendMessage = async () => {
        if (!input.trim()) return;

        console.log(`INPUT: ${input}`);
        console.log(`ID: ${id}`);

        setMessages((prev) => [
            ...prev,
            { type: "user", text: input },
        ]);

        setInput("");

        const response = await queryRFP(input, id);

        console.log("RESPONSE");
        console.log(response);

        if (response.error === undefined) {
            setMessages((prev) => [
                ...prev,
                { type: "bot", text: response.answer },
            ]);
        } else {
            setMessages((prev) => [
                ...prev,
                { type: "bot", text: response.error},
            ]);
        }
    };

    try {
      // 🔹 Call FastAPI endpoint
      const response = await evaluateLLM(id, input, input, 5);

    return (
        <div className="chat-page">
            <Navbar />
            <div className="chat-title">
                <h2>{title}</h2>
            </div>
            <div className="chat-container">
                <div className="chat-box">
                    {messages.map((msg, idx) => (
                        <div
                            key={idx}
                            className={`chat-message ${msg.type}`}
                            >
                            {msg.type === "bot"
                            ? <MarkdownView md={msg.text} />
                            : msg.text}
                        </div>
                    ))}
                    <div ref={chatEndRef} />
                </div>
                <div className="chat-input-container">
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
