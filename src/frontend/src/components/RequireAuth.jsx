import React from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const RequireAuth = () => {
  const location = useLocation();
  const { user, isAuthorized, isLoading } = useAuth();

  if (isLoading) {
    return null;
  }

  if (!user || !isAuthorized) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <Outlet />;
};

export default RequireAuth;


