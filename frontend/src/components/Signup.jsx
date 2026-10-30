
import { useState } from "react";
import { supabase } from "../lib/supabase";

export default function Signup({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function handleSignup(e) {
    e.preventDefault();
    setMessage("");
    setError("");

    if (password.length < 8) {
      setError("Password must contain at least 8 characters.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);

    try {
      const { data, error } = await supabase.auth.signUp({
        email: email.trim(),
        password,
        options: {
          emailRedirectTo: window.location.origin,
        },
      });

      if (error) throw error;

      if (data.session) {
        setMessage("Account created successfully!");
      } else {
        setMessage(
          "Account created! Please check your email and confirm your account before signing in."
        );
      }
    } catch (err) {
      setError(err.message || "Unable to create account.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <section className="auth-brand">
        <div className="auth-brand-logo">C</div>
        <h1>Clarify<span>SQL</span></h1>
        <p className="brand-tagline">Adaptive Clarification Engine</p>
        <p className="brand-description">
          Start exploring databases using natural language.
          Let AI help you understand your data.
        </p>
        <div className="brand-features">
          <span>Intelligent clarification</span>
          <span>Schema understanding</span>
          <span>Validated SQL generation</span>
        </div>
      </section>

      <section className="auth-form-section">
        <form className="auth-card" onSubmit={handleSignup}>
          <div className="auth-heading">
            <h2>Create account</h2>
            <p>Join the ClarifySQL workspace</p>
          </div>

          <label>Email address</label>
          <input
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            required
          />

          <label>Password</label>
          <input
            type="password"
            placeholder="Create a password (8+ characters)"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="new-password"
            required
            minLength={8}
          />

          <label>Confirm password</label>
          <input
            type="password"
            placeholder="Enter password again"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            autoComplete="new-password"
            required
          />

          {error && <div className="auth-message">{error}</div>}
          {message && <div className="auth-success">{message}</div>}

          <button
            type="submit"
            className="auth-primary-button"
            disabled={loading}
          >
            {loading ? "Creating account..." : "Create Account →"}
          </button>

          <p className="auth-switch">
            Already have an account?
            <button type="button" onClick={onLogin}>
              Sign In
            </button>
          </p>
        </form>
      </section>
    </div>
  );
}
