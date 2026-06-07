import { useState } from "react";
import { api } from "../api/client";

interface FeedbackButtonsProps {
  token: string;
  sessionId: string;
  query: string;
}

export function FeedbackButtons({ token, sessionId, query }: FeedbackButtonsProps) {
  const [status, setStatus] = useState<"helpful" | "not-helpful" | "">();

  async function send(helpful: boolean) {
    setStatus("");
    try {
      await api.feedback(token, { session_id: sessionId, query, helpful });
      setStatus(helpful ? "helpful" : "not-helpful");
      setTimeout(() => setStatus(""), 3000);
    } catch { setStatus(""); }
  }

  return (
    <div className="feedback-container">
      <button
        className={`feedback-btn ${status === "helpful" ? "clicked" : ""}`}
        onClick={() => send(true)}
        type="button"
      >
        <span className="feedback-icon">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M14 9V5a3 3 0 00-3-3l-4 9v11h11.28a2 2 0 002-1.7l1.38-9a2 2 0 00-2-2.3H14z"/>
            <path d="M7 22H4a2 2 0 01-2-2v-7a2 2 0 012-2h3"/>
          </svg>
        </span>
        Helpful
      </button>
      <button
        className={`feedback-btn ${status === "not-helpful" ? "clicked" : ""}`}
        onClick={() => send(false)}
        type="button"
      >
        <span className="feedback-icon">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M10 15v4a3 3 0 003 3l4-9V2H5.72a2 2 0 00-2 1.7l-1.38 9a2 2 0 002 2.3H10z"/>
            <path d="M17 2h2.67A2.31 2.31 0 0122 4v7a2.31 2.31 0 01-2.33 2H17"/>
          </svg>
        </span>
        Not helpful
      </button>
      {status && (
        <span className={`feedback-status ${status}`}>
          {status === "helpful" ? "Thanks for your feedback" : "Noted, we'll improve"}
        </span>
      )}
    </div>
  );
}
