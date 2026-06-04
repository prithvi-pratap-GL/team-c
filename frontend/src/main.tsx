import React, { useMemo, useState } from "react";
import ReactDOM from "react-dom/client";
import { LoginResponse } from "./api/client";
import { LoginForm } from "./components/LoginForm";
import { ChatPage } from "./pages/ChatPage";
import { UploadPage } from "./pages/UploadPage";
import "./styles.css";

type View = "chat" | "documents";

function App() {
  const [token, setToken] = useState<string>(() => localStorage.getItem("rag_token") ?? "");
  const [profile, setProfile] = useState<LoginResponse | null>(() => {
    const stored = localStorage.getItem("rag_profile");
    return stored ? (JSON.parse(stored) as LoginResponse) : null;
  });
  const [view, setView] = useState<View>("chat");
  const [isSigningOut, setIsSigningOut] = useState(false);

  const isAuthenticated = Boolean(token && profile);
  const departmentLabel = useMemo(
    () => profile?.departments_allowed.map((department) => department.replace("_", " ")).join(", ") ?? "",
    [profile],
  );

  function handleLogin(accessToken: string, nextProfile: LoginResponse) {
    setToken(accessToken);
    setProfile(nextProfile);
    localStorage.setItem("rag_token", accessToken);
    localStorage.setItem("rag_profile", JSON.stringify(nextProfile));
  }

  function logout() {
    setIsSigningOut(true);
    setTimeout(() => {
      setToken("");
      setProfile(null);
      localStorage.removeItem("rag_token");
      localStorage.removeItem("rag_profile");
      setIsSigningOut(false);
    }, 1000);
  }

  if (!isAuthenticated || !profile) {
    return <LoginForm onLogin={handleLogin} />;
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Document Management</p>
          <h1>Knowledge Base</h1>
        </div>
        {/* For trial purpose: Sign out button in topbar */}
        <button
          onClick={logout}
          type="button"
          className={`logout-button ${isSigningOut ? "signing-out" : ""}`}
          title="Sign out"
          disabled={isSigningOut}
        >
          {isSigningOut ? "Signing out..." : "Sign out"}
        </button>
      </header>

      <nav className="tabs">
        <div>
          <button className={view === "chat" ? "active" : ""} onClick={() => setView("chat")} type="button">
            Chat
          </button>
          <button className={view === "documents" ? "active" : ""} onClick={() => setView("documents")} type="button">
            Documents
          </button>
        </div>
        {/* For trial purpose: Avatar with user initial in tabs right corner */}
        <div className="user-avatar" title={`User: ${profile.role}`}>
          {profile.role.charAt(0).toUpperCase()}
        </div>
      </nav>

      {view === "chat" ? (
        <ChatPage token={token} allowedDepartments={profile.departments_allowed} />
      ) : (
        <UploadPage token={token} isAdmin={profile.role === "admin"} />
      )}

      {/* Fixed Footer Disclaimer */}
      <footer className="app-footer">
        Knowledge Assistant can make mistakes. Double-check for your responses.
      </footer>
    </main>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
