import React from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "../components/Navbar";
import "./RFPsPage.css";
import { fetchRFPs } from "../SupaBase/fetchRFPs";


// insert RFPs here from database we can add stuff like unscored vs scored in the future
const cardsData = await fetchRFPs();

const RFPsPage = () => {
  const navigate = useNavigate();

  const handleCardClick = (card) => {
  navigate(`/chat/${card.title}`, { state: { title: card.title } });
//   navigate(`/dashboard`, { state: { title: card.title } });
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
			</div>
			))}
		</div>
		</div>
	</div>
  );
};

export default RFPsPage;