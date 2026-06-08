import { useEffect, useRef, useState } from "react";
import { api, ChatSession } from "../api/client";

interface SidebarProps {
  token: string;
  sessions: ChatSession[];
  activeSessionId: number | null;
  onNewChat: () => void;
  onSelectSession: (session: ChatSession) => void;
  onDeleteSession: (sessionId: number) => void;
  onProfileClick: () => void;
  username: string;
  role: string;
}

export function Sidebar({
  token,
  sessions,
  activeSessionId,
  onNewChat,
  onSelectSession,
  onDeleteSession,
  onProfileClick,
  username,
  role,
}: SidebarProps) {
  const [menuOpenId, setMenuOpenId] = useState<number | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleOutsideClick(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpenId(null);
      }
    }
    document.addEventListener("mousedown", handleOutsideClick);
    return () => document.removeEventListener("mousedown", handleOutsideClick);
  }, []);

  const initials = username.slice(0, 2).toUpperCase();

  return (
    <aside className="sidebar">
      {/* Brand */}
      <div className="sidebar-brand">
        <div className="topbar-logo">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
          </svg>
        </div>
        <span className="topbar-title">Kbase</span>
      </div>

      {/* New Chat button */}
      <button className="new-chat-btn" onClick={onNewChat} type="button">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
          <path d="M12 5v14M5 12h14"/>
        </svg>
        New Chat
      </button>

      {/* Session list */}
      <div className="sidebar-sessions">
        {sessions.length === 0 ? (
          <p className="sidebar-empty">No conversations yet</p>
        ) : (
          <>
            <p className="sidebar-section-label">Recent</p>
            {sessions.map(session => (
              <div
                key={session.id}
                className={`sidebar-session ${session.id === activeSessionId ? "active" : ""}`}
                onClick={() => onSelectSession(session)}
              >
                <span className="session-title">{session.title}</span>
                <button
                  className="session-menu-btn"
                  type="button"
                  onClick={e => {
                    e.stopPropagation();
                    setMenuOpenId(menuOpenId === session.id ? null : session.id);
                  }}
                  title="More options"
                >
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                    <circle cx="5" cy="12" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="19" cy="12" r="2"/>
                  </svg>
                </button>
                {menuOpenId === session.id && (
                  <div className="session-dropdown" ref={menuRef} onClick={e => e.stopPropagation()}>
                    <button
                      className="session-dropdown-item danger"
                      type="button"
                      onClick={() => {
                        setMenuOpenId(null);
                        onDeleteSession(session.id);
                      }}
                    >
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/>
                      </svg>
                      Delete
                    </button>
                  </div>
                )}
              </div>
            ))}
          </>
        )}
      </div>

      {/* Profile footer */}
      <div className="sidebar-footer">
        <button className="sidebar-profile-btn" onClick={onProfileClick} type="button">
          <div className="user-avatar small">{initials}</div>
          <div className="sidebar-profile-info">
            <span className="sidebar-profile-name">{username}</span>
            <span className="sidebar-profile-role">{role}</span>
          </div>
        </button>
      </div>
    </aside>
  );
}
