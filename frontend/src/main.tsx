import React, { useMemo, useState, useEffect } from "react";
import ReactDOM from "react-dom/client";
import { LoginResponse } from "./api/client";
import { LoginForm } from "./components/LoginForm";
import { ChatPage } from "./pages/ChatPage";
import { UploadPage } from "./pages/UploadPage";
import "./styles.css";

type View = "chat" | "documents";
type ThemeMode = "dark" | "light" | "system";

/* ── No-flash theme injection (runs synchronously before paint) ── */
const themeScript = `
(function(){
  var s = localStorage.getItem("rag_theme") || "system";
  var dark = s === "dark" || (s === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches);
  document.documentElement.setAttribute("data-theme", dark ? "dark" : "light");
})();
`;

function useTheme() {
  const [mode, setMode] = useState<ThemeMode>(() => {
    return (localStorage.getItem("rag_theme") as ThemeMode) || "system";
  });

  const resolved = useMemo<"dark" | "light">(() => {
    if (mode === "system") {
      return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }
    return mode;
  }, [mode]);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", resolved);
    localStorage.setItem("rag_theme", mode);
  }, [mode, resolved]);

  function toggle() {
    setMode(prev => prev === "dark" ? "light" : "dark");
  }

  return { mode, resolved, toggle };
}

function ThemeToggle({ resolved, onToggle }: { resolved: "dark"|"light"; onToggle: () => void }) {
  return (
    <button
      className="theme-toggle"
      onClick={onToggle}
      title={`Switch to ${resolved === "dark" ? "light" : "dark"} mode`}
      aria-label="Toggle theme"
    >
      <span className="theme-toggle-knob">
        {resolved === "dark" ? "🌙" : "☀️"}
      </span>
    </button>
  );
}

function AtmosphericBg() {
  return (
    <>
      <div className="bg-atmosphere">
        <div className="bg-orb bg-orb-1" />
        <div className="bg-orb bg-orb-2" />
        <div className="bg-orb bg-orb-3" />
      </div>
      <div className="bg-grain" />
    </>
  );
}

function App() {
  const [token, setToken] = useState<string>(() => localStorage.getItem("rag_token") ?? "");
  const [profile, setProfile] = useState<LoginResponse | null>(() => {
    const stored = localStorage.getItem("rag_profile");
    return stored ? (JSON.parse(stored) as LoginResponse) : null;
  });
  const [view, setView] = useState<View>("chat");
  const [isSigningOut, setIsSigningOut] = useState(false);
  const { resolved, toggle } = useTheme();

  const isAuthenticated = Boolean(token && profile);

  function handleLogin(accessToken: string, nextProfile: LoginResponse) {
    setToken(accessToken);
    setProfile(nextProfile);
    localStorage.setItem("rag_token", accessToken);
    localStorage.setItem("rag_profile", JSON.stringify(nextProfile));
  }

  function logout() {
    setIsSigningOut(true);
    setTimeout(() => {
      setToken(""); setProfile(null);
      localStorage.removeItem("rag_token");
      localStorage.removeItem("rag_profile");
      setIsSigningOut(false);
    }, 800);
  }

  if (!isAuthenticated || !profile) {
    return (
      <div className="app-content">
        <AtmosphericBg />
        <LoginForm onLogin={handleLogin} />
        <ThemeToggle resolved={resolved} onToggle={toggle} />
      </div>
    );
  }

  const initials = profile.role.charAt(0).toUpperCase();

  return (
    <div className="app-content">
      <AtmosphericBg />
      <main className="app-shell">
        {/* Topbar */}
        <header className="topbar">
          <div className="topbar-brand">
            <div className="topbar-logo">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
              </svg>
            </div>
            <span className="topbar-title">Kbase</span>
          </div>
          <div className="topbar-right">
            <div className="user-avatar" title={`Role: ${profile.role}`}>{initials}</div>
            <button
              onClick={logout}
              type="button"
              className={`logout-button ${isSigningOut ? "signing-out" : ""}`}
              disabled={isSigningOut}
            >
              {isSigningOut ? "Signing out…" : "Sign out"}
            </button>
          </div>
        </header>

        {/* Nav tabs */}
        <nav className="tabs">
          <div>
            <button className={view === "chat" ? "active" : ""} onClick={() => setView("chat")} type="button">
              Chat
            </button>
            <button className={view === "documents" ? "active" : ""} onClick={() => setView("documents")} type="button">
              Documents
            </button>
          </div>
        </nav>

        {view === "chat" ? (
          <ChatPage token={token} allowedDepartments={profile.departments_allowed} />
        ) : (
          <UploadPage token={token} isAdmin={profile.role === "admin"} />
        )}

        <footer className="app-footer">
          Knowledge Assistant may make mistakes — verify important information against source documents.
        </footer>
      </main>
      <ThemeToggle resolved={resolved} onToggle={toggle} />
    </div>
  );
}

/* Inject no-flash theme script */
const scriptEl = document.createElement("script");
scriptEl.textContent = themeScript;
document.head.prepend(scriptEl);

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
