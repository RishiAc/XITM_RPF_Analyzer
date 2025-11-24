import React from "react";
import "./MetricCircle.css";

const MetricCircle = ({ value, max, label, color }) => {
  const percentage = Math.min((value / max) * 100, 100);
  const radius = 45;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percentage / 100) * circumference;

  return (
    <div className="metric-circle-container">
      <div className="metric-circle-wrapper">
        <svg className="metric-circle-svg" viewBox="0 0 100 100">
          {/* Background circle */}
          <circle
            className="metric-circle-bg"
            cx="50"
            cy="50"
            r={radius}
            fill="none"
            stroke="#e5e5e6"
            strokeWidth="8"
          />
          {/* Progress circle */}
          <circle
            className="metric-circle-progress"
            cx="50"
            cy="50"
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth="8"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            transform="rotate(-90 50 50)"
            style={{
              transition: "stroke-dashoffset 0.5s ease-in-out",
            }}
          />
        </svg>
        <div className="metric-circle-content">
          <span className="metric-value">{value}</span>
          <span className="metric-max">/{max}</span>
        </div>
      </div>
      <span className="metric-label">{label}</span>
    </div>
  );
};

export default MetricCircle;

