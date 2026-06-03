import { FormEvent, useState } from "react";
import { api, LoginResponse } from "../api/client";

interface LoginFormProps {
  onLogin: (token: string, profile: LoginResponse) => void;
}

export function LoginForm({ onLogin }: LoginFormProps) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin123");
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
    <main className="login-screen">
      <form className="login-panel" onSubmit={submit}>
        <div>
          <p className="eyebrow">Secure Knowledge Access</p>
          <h1>Enterprise RAG Assistant</h1>
        </div>

        <label>
          Username
          <input value={username} onChange={(event) => setUsername(event.target.value)} />
        </label>

        <label>
          Password
          <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
        </label>

        {error && <p className="error-text">{error}</p>}

        <button className="primary-button" disabled={loading} type="submit">
          {loading ? "Signing in..." : "Sign in"}
        </button>

        <div className="demo-users">
          <span>admin / admin123</span>
          <span>alice_hr / hr123</span>
          <span>bob_eng / eng123</span>
        </div>
      </form>
    </main>
  );
}
