import React from "react";
import "./Navbar.css";
import XITM_logo from "../assets/XITM_logo.png";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";

const Navbar = () => {
  const navigate = useNavigate();
  const { user, isLoading, signOut } = useAuth();

  const handleLogout = async () => {
    await signOut();
    navigate("/login");
  };

  return (
    <nav className="navbar">
      <div className="logo">
        <img src={XITM_logo} alt="XITM Logo" className="logo-img" />
      </div>
      <div className="nav-links">
        <a href="/">Home</a>
        <a href="/RFPs">RFPs</a>
        {!isLoading && user ? (
          <button className="logout-button" onClick={handleLogout}>
            Log out
          </button>
        ) : (
          <a href="/login">Login</a>
        )}
      </div>
    </nav>
  );
};

export default Navbar;