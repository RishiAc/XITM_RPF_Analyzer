import React from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  Outlet,
} from "react-router-dom";
import Home from "./pages/Home";
import RFPsPage from "./pages/RFPsPage";
import ChatPage from "./pages/ChatPage";
import Dashboard from "./pages/Dashboard";
import KnowledgeBasePage from "./pages/KnowledgeBasePage";
import LoginPage from "./pages/LoginPage";
import SignupPage from "./pages/SignupPage";
import ResetPasswordPage from "./pages/ResetPasswordPage";
import RequireAuth from "./components/RequireAuth";
import { useAuth } from "./context/AuthContext";

const PublicOnlyRoute = () => {
  const { user, isAuthorized, isLoading } = useAuth();

  if (isLoading) return null;
  if (user && isAuthorized) return <Navigate to="/" replace />;
  return <Outlet />;
};


function App() {
  return (
    <Router>
      {/* <nav style={{ padding: "10px", borderBottom: "1px solid #ccc" }}>
        <Link to="/" style={{ marginRight: "10px" }}>Home</Link>
      </nav> */}

      <Routes>
        <Route element={<PublicOnlyRoute />}>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
        </Route>

        <Route path="/reset-password" element={<ResetPasswordPage />} />

        <Route element={<RequireAuth />}>
          <Route path="/" element={<Home />} />
          <Route path="/rfps" element={<RFPsPage />} />
          <Route path="/chat/:id" element={<ChatPage />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/knowledge" element={<KnowledgeBasePage />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
