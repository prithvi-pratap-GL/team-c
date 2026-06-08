import React, { useCallback, useEffect, useMemo, useState } from "react";
import ReactDOM from "react-dom/client";
import { api, ChatSession, LoginResponse } from "./api/client";
import { ChatWindow } from "./components/ChatWindow";
import { LoginForm } from "./components/LoginForm";
import { ProfileModal } from "./components/ProfileModal";
import { Sidebar } from "./components/Sidebar";
import { UploadPage } from "./pages/UploadPage";
import "./styles.css";

type View = "chat" | "documents";
type ThemeMode = "dark" | "light" | "system";

/* ── No-flash theme injection ── */
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
    if (mode === "system") return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    return mode;
  }, [mode]);
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", resolved);
    localStorage.setItem("rag_theme", mode);
  }, [mode, resolved]);
  function toggle() { setMode(prev => prev === "dark" ? "light" : "dark"); }
  return { mode, resolved, toggle };
}

function ThemeToggle({ resolved, onToggle }: { resolved: "dark" | "light"; onToggle: () => void }) {
  return (
    <button
      className="theme-toggle-inline"
      onClick={onToggle}
      title={`Switch to ${resolved === "dark" ? "light" : "dark"} mode`}
      aria-label="Toggle theme"
    >
      {resolved === "dark" ? "☀️" : "🌙"}
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

/* ── Validate token by calling /users/me ── */
async function validateToken(token: string): Promise<boolean> {
  try {
    await api.getProfile(token);
    return true;
  } catch {
    return false;
  }
}

function App() {
  const [token, setToken] = useState<string>("");
  const [profile, setProfile] = useState<LoginResponse | null>(null);
  const [authChecked, setAuthChecked] = useState(false); // prevent flash
  const [view, setView] = useState<View>("chat");
  const [showProfile, setShowProfile] = useState(false);
  const { resolved, toggle } = useTheme();

  // Session state
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSession, setActiveSession] = useState<ChatSession | null>(null);
  const [sessionsLoaded, setSessionsLoaded] = useState(false);

  // On mount: validate stored token before showing app
  useEffect(() => {
    const storedToken = localStorage.getItem("rag_token") ?? "";
    const storedProfile = localStorage.getItem("rag_profile");

    if (!storedToken || !storedProfile) {
      // Nothing stored — show login
      setAuthChecked(true);
      return;
    }

    // Validate token against the server
    validateToken(storedToken).then(valid => {
      if (valid) {
        setToken(storedToken);
        setProfile(JSON.parse(storedProfile) as LoginResponse);
      } else {
        // Token expired or invalid — clear and show login
        localStorage.removeItem("rag_token");
        localStorage.removeItem("rag_profile");
      }
      setAuthChecked(true);
    });
  }, []);

  // Load sessions once authenticated
  useEffect(() => {
    if (!token || !profile || sessionsLoaded) return;
    api.listSessions(token)
      .then(list => {
        setSessions(list);
        setSessionsLoaded(true);
        if (list.length > 0) setActiveSession(list[0]);
      })
      .catch(() => setSessionsLoaded(true));
  }, [token, profile, sessionsLoaded]);

  function handleLogin(accessToken: string, nextProfile: LoginResponse) {
    setToken(accessToken);
    setProfile(nextProfile);
    localStorage.setItem("rag_token", accessToken);
    localStorage.setItem("rag_profile", JSON.stringify(nextProfile));
    setSessionsLoaded(false);
    setSessions([]);
    setActiveSession(null);
  }

  function logout() {
    setToken("");
    setProfile(null);
    setSessions([]);
    setActiveSession(null);
    setSessionsLoaded(false);
    setShowProfile(false);
    localStorage.removeItem("rag_token");
    localStorage.removeItem("rag_profile");
  }

  async function handleNewChat() {
    try {
      const session = await api.createSession(token);
      setSessions(prev => [session, ...prev]);
      setActiveSession(session);
      setView("chat");
    } catch (e) {
      console.error("Failed to create session", e);
    }
  }

  function handleSelectSession(session: ChatSession) {
    setActiveSession(session);
    setView("chat");
  }

  async function handleDeleteSession(sessionId: number) {
    try {
      await api.deleteSession(token, sessionId);
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      if (activeSession?.id === sessionId) {
        const remaining = sessions.filter(s => s.id !== sessionId);
        setActiveSession(remaining[0] ?? null);
      }
    } catch (e) {
      console.error("Failed to delete session", e);
    }
  }

  const handleSessionTitleChange = useCallback((_sessionId: number, _sid: string) => {
    api.listSessions(token).then(list => {
      setSessions(list);
      setActiveSession(prev => prev ? (list.find(s => s.id === prev.id) ?? prev) : prev);
    }).catch(() => {});
  }, [token]);

  // Show nothing until auth check completes (prevents flash of wrong page)
  if (!authChecked) {
    return (
      <div className="app-content">
        <AtmosphericBg />
        <div className="auth-checking">
          <span className="spinner" />
        </div>
      </div>
    );
  }

  const isAuthenticated = Boolean(token && profile);

  if (!isAuthenticated || !profile) {
    return (
      <div className="app-content">
        <AtmosphericBg />
        <LoginForm onLogin={handleLogin} />
      </div>
    );
  }

  const displayName = profile.role === "admin"
    ? "admin"
    : profile.departments_allowed[0]?.replace("_", " ") ?? profile.role;

  return (
    <div className="app-content">
      <AtmosphericBg />

      {showProfile && (
        <ProfileModal
          token={token}
          onClose={() => setShowProfile(false)}
          onLogout={logout}
        />
      )}

      <main className="app-shell-sidebar">
        <Sidebar
          token={token}
          sessions={sessions}
          activeSessionId={activeSession?.id ?? null}
          onNewChat={handleNewChat}
          onSelectSession={handleSelectSession}
          onDeleteSession={handleDeleteSession}
          onProfileClick={() => setShowProfile(true)}
          username={displayName}
          role={profile.role}
        />

        <div className="main-area">
          {/* Topbar */}
          <header className="topbar">
            <div className="topbar-brand">
              {activeSession ? (
                <span className="topbar-session-title">{activeSession.title}</span>
              ) : (
                <span className="topbar-title">Kbase</span>
              )}
            </div>
            <div className="topbar-right">
              <nav className="tabs-inline">
                <button className={view === "chat" ? "active" : ""} onClick={() => setView("chat")} type="button">Chat</button>
                <button className={view === "documents" ? "active" : ""} onClick={() => setView("documents")} type="button">Documents</button>
              </nav>
              <ThemeToggle resolved={resolved} onToggle={toggle} />
              <button
                className="topbar-avatar"
                onClick={() => setShowProfile(true)}
                title="Profile"
                type="button"
              >
                {profile.role.charAt(0).toUpperCase()}
              </button>
              <button
                className="logout-button"
                onClick={logout}
                type="button"
              >
                Sign out
              </button>
            </div>
          </header>

          {view === "chat" ? (
            <ChatWindow
              token={token}
              allowedDepartments={profile.departments_allowed}
              activeSession={activeSession}
              onSessionTitleChange={handleSessionTitleChange}
            />
          ) : (
            <UploadPage token={token} isAdmin={profile.role === "admin"} />
          )}

          <footer className="app-footer">
            Knowledge Assistant may make mistakes — verify important information against source documents.
          </footer>
        </div>
      </main>
    </div>
  );
}

const scriptEl = document.createElement("script");
scriptEl.textContent = themeScript;
document.head.prepend(scriptEl);

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
