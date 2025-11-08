import React, { useState } from "react";
import "./Source.css";

const Source = ({ text }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => {
        setCopied(false);
      }, 2000);
    } catch (err) {
      console.error("Failed to copy source", err);
    }
  };

  return (
    <div className="source-card">
      <div className="source-card__text">{text}</div>
      <button
        type="button"
        className="source-card__button"
        onClick={handleCopy}
        aria-label={copied ? "Source copied" : "Copy source"}
      >
        {copied ? "✓" : "Copy"}
      </button>
    </div>
  );
};

export default Source;

