import React from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "../components/Navbar";
import "./RFPsPage.css";


// insert RFPs here from database we can add stuff like unscored vs scored in the future
const cardsData = [
  { id: 1, title: "RFP A", description: "Chat about A" },
  { id: 2, title: "RFP B", description: "Chat about B" },
  { id: 3, title: "RFP C", description: "Chat about C" },
  { id: 4, title: "RFP D", description: "Chat about D" },
  { id: 5, title: "RFP E", description: "Chat about E" },
  { id: 6, title: "RFP F", description: "Chat about F" },
  { id: 7, title: "RFP G", description: "Chat about G" },
  { id: 8, title: "RFP H", description: "Chat about H" },
  { id: 9, title: "RFP I", description: "Chat about I" },
  { id: 10, title: "RFP J", description: "Chat about J" },
  { id: 11, title: "RFP K", description: "Chat about K" },
  { id: 12, title: "RFP L", description: "Chat about L" },
  { id: 13, title: "RFP M", description: "Chat about M" },
  { id: 14, title: "RFP N", description: "Chat about N" },
  { id: 15, title: "RFP O", description: "Chat about O" },
  { id: 16, title: "RFP P", description: "Chat about P" },
  { id: 17, title: "RFP Q", description: "Chat about Q" },
  { id: 18, title: "RFP R", description: "Chat about R" },
  { id: 19, title: "RFP S", description: "Chat about S" },
  { id: 20, title: "RFP T", description: "Chat about T" },
];

const RFPsPage = () => {
  const navigate = useNavigate();

  const handleCardClick = (card) => {
  // Pass title via state
  navigate(`/chat/${card.id}`, { state: { title: card.title } });
  };

  return (
	<div className="cards-page scrollable">
		<div className="home-container">
		<Navbar />
		<h1 className="page-title">RFPs</h1>
		<div className="cards-container">
			{cardsData.map((card) => (
			<div
				key={card.id}
				className="card"
				onClick={() => handleCardClick(card)}
			>
				<h2>{card.title}</h2>
				<p>{card.description}</p>
			</div>
			))}
		</div>
		</div>
	</div>
  );
};

export default RFPsPage;