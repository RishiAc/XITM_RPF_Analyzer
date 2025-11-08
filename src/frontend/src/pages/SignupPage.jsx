import React, { useState } from "react";
import "./SignupPage.css";
import Navbar from "../components/Navbar";
import { authConfig, isEmailAllowed } from "../config/authConfig";
import { supabase } from "../SupaBase/supabaseClient";

const SignupPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [emailError, setEmailError] = useState("");
  const [generalError, setGeneralError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!isEmailAllowed(email)) {
      setEmailError(
        `Signup with your @${authConfig.allowedDomain} email or contact an administrator.`
      );
      return;
    }
    setEmailError("");

    if (password !== confirmPassword) {
      setGeneralError("Passwords do not match.");
      return;
    }

    setGeneralError("");
    setSuccessMessage("");
    setIsSubmitting(true);

    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          emailRedirectTo: `${window.location.origin}/login`,
        },
      });

      if (error) {
        setGeneralError(error.message);
        return;
      }

      if (data?.user) {
        setSuccessMessage(
          "Account created! Check your email for a verification code."
        );
      }
    } catch (err) {
      console.error("Supabase sign-up error:", err);
      setGeneralError("Unexpected error during signup. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="signup-container">
      <Navbar />

      <div className="signup-content">
        <section className="signup-hero">
          <h1>
            Join <span>XITM RFP Analyzer</span>
          </h1>
          <p>
            Create your account to upload RFPs, collaborate with your team, and
            uncover insights faster.
          </p>
        </section>

        <section className="signup-card">
          <h2>Create Account</h2>
          <form onSubmit={handleSubmit}>
            <label htmlFor="signup-email">Email</label>
            <input
              id="signup-email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
            />
            {emailError && <p className="signup-error">{emailError}</p>}

            <label htmlFor="signup-password">Password</label>
            <input
              id="signup-password"
              type="password"
              placeholder="Create a password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="new-password"
            />

            <label htmlFor="signup-confirm-password">Confirm Password</label>
            <input
              id="signup-confirm-password"
              type="password"
              placeholder="Confirm password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              autoComplete="new-password"
            />

            {generalError && <p className="signup-error">{generalError}</p>}
            {successMessage && (
              <p className="signup-success">{successMessage}</p>
            )}

            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Creating account..." : "Create Account"}
            </button>
          </form>

          <div className="signup-footer">
            <span>Already have an account?</span>
            <a href="/login">Sign in</a>
          </div>
        </section>
      </div>
    </div>
  );
};

export default SignupPage;


