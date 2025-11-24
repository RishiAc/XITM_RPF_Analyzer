import React from "react";
import "./Source.css";

const Source = ({ text }) => {
  return (
    <div className="source-item">
      <p className="source-text">{text}</p>
    </div>
  );
};

export default Source;

