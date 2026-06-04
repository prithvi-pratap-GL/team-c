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
      // Auto-clear status after 3 seconds
      setTimeout(() => setStatus(""), 3000);
    } catch (err) {
      setStatus("");
    }
  }

  return (
    <div className="feedback-container">
      <div className="feedback-row">
        <button
          className={`feedback-btn helpful-btn ${status === "helpful" ? "clicked" : ""}`}
          onClick={() => send(true)}
          type="button"
          title="Helpful"
        >
          <span className="feedback-icon">👍</span>
          <span className="feedback-label">Helpful</span>
        </button>
        <button
          className={`feedback-btn not-helpful-btn ${status === "not-helpful" ? "clicked" : ""}`}
          onClick={() => send(false)}
          type="button"
          title="Not helpful"
        >
          <span className="feedback-icon">👎</span>
          <span className="feedback-label">Not helpful</span>
        </button>
      </div>

      {status && (
        <div className={`feedback-status ${status}`}>
          {status === "helpful" ? "Thanks" : "Got it"}
        </div>
      )}
    </div>
  );
}
