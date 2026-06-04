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
    <div className="mock-login-container">
      <div className="mock-login-card">
        <div className="login-header">
          <p className="eyebrow">👋 Welcome to</p>
          <h1 className="welcome-title">Knowledge Assistant</h1>
          <p className="welcome-subtitle">Test environment using mock credentials</p>
        </div>

        <form className="mock-login-form" onSubmit={submit}>
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              placeholder="Enter your username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <div className="password-input-wrapper">
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="form-input"
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword(!showPassword)}
                title={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? "Hide" : "Show"}
              </button>
            </div>
          </div>

          {error && <p className="error-message">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="login-button"
          >
            {loading ? "Signing in..." : "Log In"}
          </button>
        </form>

        <div className="test-credentials">
          <p className="credentials-title">📝 Test Credentials (For Testing Only)</p>
          <p className="credentials-note">This is a test environment. Use the credentials below to explore the application:</p>
          <div className="credentials-list">
            <code>username: admin          password: admin123</code>
            <code>username: alice_hr       password: hr123</code>
            <code>username: bob_eng        password: eng123</code>
          </div>
        </div>
      </div>
    </div>
  );
}
