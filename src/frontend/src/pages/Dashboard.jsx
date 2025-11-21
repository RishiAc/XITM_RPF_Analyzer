import React from "react";
import { useLocation, useNavigate } from "react-router-dom";
import Navbar from "../components/Navbar";
import ScoreCard from "../components/ScoreCard";
import "./Dashboard.css";

const DashboardPage = () => {
  const sampleScore = 75;

  const location = useLocation();
  const navigate = useNavigate();
  
  const { state } = location;
  const rfpTitle = state?.title || null;

  const handleAskQuestionsClick = () => {
    if (rfpTitle !== null) {
      navigate(`/chat/${rfpTitle}`, { state: { title: rfpTitle } });
    } else {
      alert("RFP ID not found");
    }
  };

  const handlePhaseClick = (phase) => {
    alert(`You clicked: ${phase}`);
  };

  return (
    <div className="dashboard-container">
      {/* Navbar at the top */}
      <Navbar />

      {/* Dashboard header */}
      <header className="dashboard-header">
        <h1>{rfpTitle}</h1>
      </header>

      {/* Main dashboard layout */}
      <div className="dashboard-main">
        {/* Left column */}
        <div className="dashboard-left">
          <div
            className="dashboard-box"
            onClick={handleAskQuestionsClick}
          >
            Ask questions about this RFP
          </div>
        </div>

        {/* Center column */}
        <div className="dashboard-center">
          <ScoreCard score={sampleScore} />
        </div>

        {/* Right column */}
        <div className="dashboard-right">
          {["Phase 1", "Phase 2", "Phase 3", "Phase 4"].map((phase) => (
            <div
              key={phase}
              className="dashboard-box"
              onClick={() => handlePhaseClick(phase)}
            >
              {phase}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
