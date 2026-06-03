import { useState } from "react";
import { api } from "../api/client";

interface FeedbackButtonsProps {
  token: string;
  sessionId: string;
  query: string;
}

export function FeedbackButtons({ token, sessionId, query }: FeedbackButtonsProps) {
  const [status, setStatus] = useState("");

  async function send(helpful: boolean) {
    setStatus("");
    try {
      await api.feedback(token, { session_id: sessionId, query, helpful });
      setStatus("Recorded");
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Failed");
    }
  }

  return (
    <div className="feedback-row">
      <button title="Helpful" onClick={() => send(true)} type="button">
        +
      </button>
      <button title="Not helpful" onClick={() => send(false)} type="button">
        -
      </button>
      {status && <span>{status}</span>}
    </div>
  );
}
