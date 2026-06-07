import { FormEvent, useState } from "react";
import { api, LoginResponse } from "../api/client";

interface LoginFormProps {
  onLogin: (token: string, profile: LoginResponse) => void;
}

export function LoginForm({ onLogin }: LoginFormProps) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin123");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const profile = await api.login(username, password);
      onLogin(profile.access_token, profile);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-root">
      {/* Left branding */}
      <div className="login-left">
        <div className="login-left-brand">
          <div className="login-logo-mark">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
              <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
            </svg>
          </div>
          <span className="login-left-brand-name">Kbase</span>
        </div>

        <div className="login-left-hero">
          <h1 className="login-headline">
            Enterprise knowledge,<br />
            <span>instantly retrieved.</span>
          </h1>
          <p className="login-subheadline">
            Semantic search across your organization's documents with RAG-powered answers and source attribution.
          </p>
          <div className="login-features">
            {[
              { title: "Hybrid retrieval", desc: "Vector + BM25 for maximum accuracy" },
              { title: "Source attribution", desc: "Every answer linked to evidence" },
              { title: "Role-based access", desc: "Department-scoped document visibility" },
            ].map(f => (
              <div key={f.title} className="login-feature">
                <div className="login-feature-dot" />
                <p className="login-feature-text">
                  <strong>{f.title}</strong> — {f.desc}
                </p>
              </div>
            ))}
          </div>
        </div>

        <p className="login-left-footer">© 2025 Kbase. Enterprise RAG Platform.</p>
      </div>

      {/* Right form */}
      <div className="login-right">
        <div className="login-glass">
          <div className="login-form-header">
            <p className="login-form-eyebrow">Secure Access</p>
            <h2 className="login-form-title">Sign in</h2>
            <p className="login-form-subtitle">Test environment — use demo credentials below</p>
          </div>

          <form className="mock-login-form" onSubmit={submit}>
            <div className="form-group">
              <label htmlFor="username">Username</label>
              <input
                id="username"
                type="text"
                placeholder="Enter username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="form-input"
                autoComplete="username"
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Password</label>
              <div className="password-input-wrapper">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Enter password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="form-input"
                  autoComplete="current-password"
                  style={{ paddingRight: "64px" }}
                />
                <button
                  type="button"
                  className="password-toggle"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? "Hide" : "Show"}
                </button>
              </div>
            </div>

            {error && <p className="error-message">{error}</p>}

            <button type="submit" disabled={loading} className="login-button">
              {loading ? "Signing in…" : "Continue"}
            </button>
          </form>

          <div className="test-credentials" style={{ marginTop: "24px" }}>
            <p className="credentials-title">Demo credentials</p>
            <div className="credentials-list">
              <code>admin       / admin123</code>
              <code>alice_hr    / hr123</code>
              <code>bob_eng     / eng123</code>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
