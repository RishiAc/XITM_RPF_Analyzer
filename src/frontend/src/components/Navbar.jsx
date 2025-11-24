import "./Navbar.css";
import XITM_logo from "../assets/XITM_logo.png";
import { useAuth } from "../context/AuthContext";
import { Link, useNavigate } from "react-router-dom";

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
        <Link to="/">Home</Link>
        <Link to="/rfps">RFPs</Link>
        <Link to="/knowledgebase">Knowledge Base</Link>
        {!isLoading && user ? (
          <button className="logout-button" onClick={handleLogout}>
            Log out
          </button>
        ) : (
          <Link to="/login">Login</Link>
        )}
      </div>
    </nav>
  );
};

export default Navbar;