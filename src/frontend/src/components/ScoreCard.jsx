import React from "react";
import "./ScoreCard.css";

const ScoreCard = ({ score }) => {
  const clampedScore = Math.max(0, Math.min(100, score));
  const radius = 60;
  const stroke = 10;
  const normalizedRadius = radius - stroke / 2;
  const circumference = 2 * Math.PI * normalizedRadius;
  const strokeDashoffset = circumference - (clampedScore / 100) * circumference;

  const hue = (clampedScore * 120) / 100;
  const color = `hsl(${hue}, 100%, 45%)`;

  return (
    <div className="score-card-circular">
      <div className="circle-container">
        <svg height={radius * 2} width={radius * 2}>
          <circle
            stroke="#eee"
            fill="transparent"
            strokeWidth={stroke}
            r={normalizedRadius}
            cx={radius}
            cy={radius}
          />
          <circle
            stroke={color}
            fill="transparent"
            strokeWidth={stroke}
            r={normalizedRadius}
            cx={radius}
            cy={radius}
            strokeDasharray={circumference + " " + circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            transform={`rotate(-90 ${radius} ${radius})`}
          />
        </svg>
        <div className="score-text-circular">
          <span>Score</span>
          <strong style={{ color }}>{clampedScore}</strong>
        </div>
      </div>
    </div>
  );
};

export default ScoreCard;
