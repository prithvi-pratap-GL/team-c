import { useEffect, useState } from "react";
import { api, UserProfile } from "../api/client";

interface ProfileModalProps {
  token: string;
  onClose: () => void;
  onLogout: () => void;
}

export function ProfileModal({ token, onClose, onLogout }: ProfileModalProps) {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getProfile(token)
      .then(setProfile)
      .catch(() => setError("Failed to load profile"))
      .finally(() => setLoading(false));
  }, [token]);

  function formatDate(iso: string) {
    return new Date(iso).toLocaleDateString("en-US", {
      year: "numeric", month: "long", day: "numeric",
    });
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-panel profile-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title">Profile</h2>
          <button className="modal-close" onClick={onClose} type="button">×</button>
        </div>

        {loading && <p className="modal-loading">Loading…</p>}
        {error && <p className="modal-error">{error}</p>}

        {profile && (
          <>
            <div className="profile-avatar-section">
              <div className="profile-avatar-lg">
                {profile.username.slice(0, 2).toUpperCase()}
              </div>
              <div>
                <p className="profile-username">{profile.username}</p>
                <span className="role-badge">{profile.role}</span>
              </div>
            </div>

            <div className="profile-fields">
              <div className="profile-field">
                <span className="profile-field-label">Username</span>
                <span className="profile-field-value">{profile.username}</span>
              </div>
              <div className="profile-field">
                <span className="profile-field-label">Role</span>
                <span className="profile-field-value">{profile.role}</span>
              </div>
              <div className="profile-field">
                <span className="profile-field-label">Departments</span>
                <span className="profile-field-value">
                  {profile.departments_allowed.map(d => d.replace("_", " ")).join(", ")}
                </span>
              </div>
              <div className="profile-field">
                <span className="profile-field-label">Member since</span>
                <span className="profile-field-value">{formatDate(profile.created_at)}</span>
              </div>
            </div>

            <div className="profile-actions">
              <button className="btn-logout-modal" onClick={onLogout} type="button">
                Sign out
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
