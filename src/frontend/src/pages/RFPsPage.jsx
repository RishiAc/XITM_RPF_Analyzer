import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "../components/Navbar";
import "./RFPsPage.css";
import { fetchRFPs } from "../SupaBase/fetchRFPs";

const RFPsPage = () => {
  const navigate = useNavigate();
  const [cardsData, setCardsData] = useState([]);

  useEffect(() => {
    fetchRFPs().then(setCardsData);
  }, []);

  const handleCardClick = (card) => {
    const rfpId = card.qdrant_doc_id ?? card.id;
    navigate(`/chat/${rfpId}`, { state: { title: card.title } });
  };

  return (
	<div className="cards-page scrollable">
		<div className="home-container">
		<Navbar />
		<h1 className="page-title">RFPs</h1>
		<div className="cards-container">
			{cardsData.map((card) => (
			<div
				key={card.qdrant_doc_id ?? card.id}
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