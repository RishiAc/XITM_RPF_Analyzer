import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import RFPsPage from "./pages/RFPsPage";
import ChatPage from "./pages/ChatPage";
import Dashboard from "./pages/Dashboard";
import KnowledgeBasePage from "./pages/KnowledgeBasePage";


function App() {
  return (
    <Router>
      {/* <nav style={{ padding: "10px", borderBottom: "1px solid #ccc" }}>
        <Link to="/" style={{ marginRight: "10px" }}>Home</Link>
      </nav> */}

      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/rfps" element={<RFPsPage />} />
        <Route path="/chat/:id" element={<ChatPage />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/knowledgebase" element={<KnowledgeBasePage />} />
      </Routes>
    </Router>
  );
}

export default App;
