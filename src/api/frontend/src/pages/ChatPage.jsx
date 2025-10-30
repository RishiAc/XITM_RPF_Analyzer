import React, { useState, useEffect, useRef } from "react";
import { useParams, useLocation } from "react-router-dom";
import Navbar from "../components/Navbar";
import "./ChatPage.css";

const ChatPage = () => {
    const { id } = useParams();
    const location = useLocation();
    const title = location.state?.title || `RFP ${id}`;

    // sample responses
    const [messages, setMessages] = useState([]);


    const [input, setInput] = useState("");
    const chatEndRef = useRef(null);

    const sendMessage = () => {
        if (!input.trim()) return;
        setMessages((prev) => [
            ...prev,
            { type: "user", text: input },
            { type: "bot", text: "This is a filler response." },
        ]);
        setInput("");
    };

    // Auto-scroll to bottom when messages update
    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

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
                            ? `Most Relevant Chunk: ${msg.text}`
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
        </div>
    );
};

export default ChatPage;
