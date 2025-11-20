import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import RFPsPage from "./pages/RFPsPage";
import ChatPage from "./pages/ChatPage";
import Dashboard from "./pages/Dashboard";
import LoginPage from "./pages/LoginPage";
import SignupPage from "./pages/SignupPage";
import RequireAuth from "./components/RequireAuth";
import KnowledgeBasePage from "./pages/KnowledgeBasePage";


function App() {
  return (
    <Router>
      {/* <nav style={{ padding: "10px", borderBottom: "1px solid #ccc" }}>
        <Link to="/" style={{ marginRight: "10px" }}>Home</Link>
      </nav> */}

      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />

        <Route element={<RequireAuth />}>
          <Route path="/" element={<Home />} />
          <Route path="/rfps" element={<RFPsPage />} />
          <Route path="/chat/:id" element={<ChatPage />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/knowledgebase" element={<KnowledgeBasePage />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
