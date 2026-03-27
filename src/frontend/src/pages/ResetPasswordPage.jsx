import React, { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import "./LoginPage.css";
import Navbar from "../components/Navbar";
import { authConfig, isEmailAllowed } from "../config/authConfig";
import { supabase } from "../SupaBase/supabaseClient";

const ResetPasswordPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [email, setEmail] = useState(searchParams.get("email") || "");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [mode, setMode] = useState("request");
  const [generalError, setGeneralError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const hasApprovedList = (authConfig.approvedEmails || []).length > 0;
  const allowedHint = hasApprovedList
    ? "an approved email address"
    : `your ${authConfig.allowedDomain} email`;

  const helperCopy = useMemo(() => {
    if (mode === "update") {
      return "Create a new password for your approved account.";
    }

    return "Enter your approved email and we will send you a password reset link.";
  }, [mode]);

  useEffect(() => {
    let isMounted = true;

    const syncRecoverySession = async () => {
      try {
        const hashParams = new URLSearchParams(window.location.hash.replace(/^#/, ""));
        const accessToken = hashParams.get("access_token");
        const refreshToken = hashParams.get("refresh_token");
        const flowType = hashParams.get("type");

        if (flowType === "recovery" && accessToken && refreshToken) {
          const { error } = await supabase.auth.setSession({
            access_token: accessToken,
            refresh_token: refreshToken,
          });

          if (error) {
            throw error;
          }

          window.history.replaceState(
            {},
            document.title,
            `${window.location.pathname}${window.location.search}`
          );
        }

        const {
          data: { session },
        } = await supabase.auth.getSession();

        if (!isMounted || !session?.user?.email) {
          return;
        }

        if (!isEmailAllowed(session.user.email)) {
          await supabase.auth.signOut();
          setGeneralError("This password reset link is not valid for an approved account.");
          setMode("request");
          return;
        }

        setEmail(session.user.email);
        setMode("update");
      } catch (error) {
        console.error("Error restoring recovery session:", error);
        if (isMounted) {
          setGeneralError("This password reset link is invalid or has expired. Request a new one below.");
          setMode("request");
        }
      }
    };

    syncRecoverySession();

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event, session) => {
      if (event === "PASSWORD_RECOVERY" || (event === "SIGNED_IN" && session?.user?.email)) {
        if (session?.user?.email && isEmailAllowed(session.user.email)) {
          setEmail(session.user.email);
          setMode("update");
          setGeneralError("");
          setSuccessMessage("");
        }
      }
    });

    return () => {
      isMounted = false;
      subscription.unsubscribe();
    };
  }, []);

  const handleRequestReset = async (event) => {
    event.preventDefault();

    if (!isEmailAllowed(email)) {
      setGeneralError(`Please use ${allowedHint}.`);
      return;
    }

    setGeneralError("");
    setSuccessMessage("");
    setIsSubmitting(true);

    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email.trim(), {
        redirectTo: `${window.location.origin}/reset-password`,
      });

      if (error) {
        setGeneralError(error.message);
        return;
      }

      setSuccessMessage("If that approved account exists, a password reset link has been sent to your email.");
    } catch (error) {
      console.error("Password reset request failed:", error);
      setGeneralError("Unexpected error sending password reset email. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUpdatePassword = async (event) => {
    event.preventDefault();

    if (password.length < 8) {
      setGeneralError("Use at least 8 characters for your new password.");
      return;
    }

    if (password !== confirmPassword) {
      setGeneralError("Passwords do not match.");
      return;
    }

    setGeneralError("");
    setSuccessMessage("");
    setIsSubmitting(true);

    try {
      const { error } = await supabase.auth.updateUser({ password });

      if (error) {
        setGeneralError(error.message);
        return;
      }

      await supabase.auth.signOut();
      setSuccessMessage("Your password has been updated. Sign in with your new password.");
      setPassword("");
      setConfirmPassword("");
      setMode("request");
      setTimeout(() => navigate("/login"), 1200);
    } catch (error) {
      console.error("Password update failed:", error);
      setGeneralError("Unexpected error updating password. Please try again.");
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
            <span>Reset Password</span>
          </h1>
          <p>{helperCopy}</p>
        </section>

        <section className="login-card">
          <h2>{mode === "update" ? "Set New Password" : "Forgot Password"}</h2>

          <form onSubmit={mode === "update" ? handleUpdatePassword : handleRequestReset}>
            <label htmlFor="reset-email">Email</label>
            <input
              id="reset-email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              autoComplete="email"
              disabled={mode === "update"}
            />

            {mode === "update" ? (
              <>
                <label htmlFor="reset-password">New Password</label>
                <input
                  id="reset-password"
                  type="password"
                  placeholder="Create a new password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  autoComplete="new-password"
                />

                <label htmlFor="reset-confirm-password">Confirm New Password</label>
                <input
                  id="reset-confirm-password"
                  type="password"
                  placeholder="Confirm new password"
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
                  autoComplete="new-password"
                />
              </>
            ) : null}

            {generalError && <p className="login-error">{generalError}</p>}
            {successMessage && <p className="login-success">{successMessage}</p>}

            <button type="submit" disabled={isSubmitting}>
              {isSubmitting
                ? mode === "update"
                  ? "Updating..."
                  : "Sending..."
                : mode === "update"
                  ? "Update Password"
                  : "Send Reset Link"}
            </button>
          </form>

          <div className="login-footer">
            <Link to="/login">Back to sign in</Link>
            <Link to="/signup">Create account</Link>
          </div>
        </section>
      </div>
    </div>
  );
};

export default ResetPasswordPage;
