import React, { useState } from "react";
import "./LoginPage.css";
import Navbar from "../components/Navbar";
import { authConfig, isEmailAllowed } from "../config/authConfig";
import { supabase } from "../SupaBase/supabaseClient";

const LoginPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [emailError, setEmailError] = useState("");
  const [generalError, setGeneralError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!isEmailAllowed(email)) {
      setEmailError(
        `Please use your @${authConfig.allowedDomain} email or contact an administrator.`
      );
      return;
    }

    setEmailError("");
    setGeneralError("");
    setIsSubmitting(true);

    try {
      const { error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) {
        setGeneralError(error.message);
        return;
      }

      // TODO: proceed to OTP verification step (handled in upcoming steps)
      console.log("Primary sign-in succeeded. Awaiting OTP verification...");
    } catch (err) {
      console.error("Supabase sign-in error:", err);
      setGeneralError("Unexpected error during sign-in. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="login-container">
      <Navbar />

      <div className="login-content">
        <section className="login-hero">
          <h1>
            <span>XITM RFP Analyzer</span>
          </h1>
          <p>
            Sign in to continue analyzing proposals, exploring insights, and
            collaborating with your team.
          </p>
        </section>

        <section className="login-card">
          <h2>Sign In</h2>
          <form onSubmit={handleSubmit}>
            <label htmlFor="login-email">Email</label>
            <input
              id="login-email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
            />
            {emailError && <p className="login-error">{emailError}</p>}

            <label htmlFor="login-password">Password</label>
            <input
              id="login-password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />

            {generalError && <p className="login-error">{generalError}</p>}

            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Signing in..." : "Continue"}
            </button>
          </form>

          <div className="login-footer">
            <span>Need an account?</span>
            <a href="/request-access">Request access</a>
          </div>
        </section>
      </div>
    </div>
  );
};

export default LoginPage;

