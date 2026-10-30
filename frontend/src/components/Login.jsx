
import { useState } from "react";
import { supabase } from "../lib/supabase";

export default function Login({ onSignup }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleLogin(e) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const { error } = await supabase.auth.signInWithPassword({
        email: email.trim(),
        password,
      });

      if (error) throw error;
    } catch (err) {
      setError(err.message || "Unable to sign in.");
    } finally {
      setLoading(false);
    }
  }

  async function handleForgotPassword() {
    setError("");

    if (!email.trim()) {
      setError("Enter your email address first.");
      return;
    }

    const { error } =
      await supabase.auth.resetPasswordForEmail(email.trim(), {
        redirectTo: window.location.origin,
      });

    if (error) setError(error.message);
    else setError("Password reset email sent. Check your inbox.");
  }

  return (
    <div className="auth-page">
      <section className="auth-brand">
        <div className="auth-brand-logo">C</div>
        <h1>Clarify<span>SQL</span></h1>
        <p className="brand-tagline">Adaptive Clarification Engine</p>

        <p className="brand-description">
          Understand natural-language questions.
          Clarify user intent.
          Generate validated SQL with AI.
        </p>

        <div className="brand-features">
          <span>Understand your query</span>
          <span>Clarify the intent</span>
          <span>Generate SQL</span>
          <span>Analyze results</span>
        </div>
      </section>

      <section className="auth-form-section">
        <form className="auth-card" onSubmit={handleLogin}>
          <div className="auth-heading">
            <h2>Welcome back</h2>
            <p>Sign in to your ClarifySQL workspace</p>
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
            placeholder="Enter your password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />

          <button
            type="button"
            className="forgot-button"
            onClick={handleForgotPassword}
          >
            Forgot password?
          </button>

          {error && <div className="auth-message">{error}</div>}

          <button
            className="auth-primary-button"
            type="submit"
            disabled={loading}
          >
            {loading ? "Signing in..." : "Sign In →"}
          </button>

          <div className="auth-divider">
            <span>or</span>
          </div>

          <p className="auth-switch">
            New to ClarifySQL?
            <button type="button" onClick={onSignup}>
              Create an account
            </button>
          </p>
        </form>
      </section>
    </div>
  );
}
