import React from "react";
import "./Navbar.css"; 

const Navbar = () => {
  return (
    <nav className="navbar">
      <div className="logo">XITM</div>
      <div className="nav-links">
        <a href="/">Home</a>
        <a href="/RFPs">RFPs</a>
      </div>
    </nav>
  );
};

export default Navbar;