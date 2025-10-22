import React from "react";
import "./Navbar.css"; 
import XITM_logo from "../assets/XITM_logo.png";

const Navbar = () => {
  return (
    <nav className="navbar">
      <div className="logo">
        <img src={XITM_logo} alt="XITM Logo" className="logo-img" />
      </div>
      <div className="nav-links">
        <a href="/">Home</a>
        <a href="/RFPs">RFPs</a>
      </div>
    </nav>
  );
};

export default Navbar;