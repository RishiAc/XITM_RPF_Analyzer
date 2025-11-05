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
          { type: "bot", text: response.answer },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          { type: "bot", text: response.error },
        ]);
      }

      // Optionally call the evaluation endpoint (if you need it)
    //   try {
    //     const evalResponse = await evaluateLLM(
    //       id,
    //       userInput,
    //       response.answer ?? userInput,
    //       5
    //     );
    //     console.log("EVAL RESPONSE");
    //     console.log(evalResponse);
    //   } catch (evalErr) {
    //     console.error("Error evaluating LLM:", evalErr);
    //   }
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
              {msg.type === "bot" ? (
                <MarkdownView md={typeof msg.text === "string" ? msg.text : String(msg.text)} />
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
      </div>
    </div>
  );
};

export default ChatPage;
