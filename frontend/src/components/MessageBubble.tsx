import { ChatResponse } from "../api/client";
import { FeedbackButtons } from "./FeedbackButtons";
import { SourceCard } from "./SourceCard";

export interface Message {
  id: string;
  role: "user" | "assistant";
  text: string;
  query?: string;
  response?: ChatResponse;
}

interface MessageBubbleProps {
  message: Message;
  token: string;
}

export function MessageBubble({ message, token }: MessageBubbleProps) {
  const isAssistant = message.role === "assistant";

  return (
    <div className={`message-row ${message.role}`}>
      <div className="message-bubble">
        <p>{message.text}</p>
        {isAssistant && message.response && (
          <>
            <div className={`confidence ${message.response.confidence}`}>{message.response.confidence}</div>
            {message.response.sources.length > 0 && (
              <div className="sources-list">
                {message.response.sources.map((source) => (
                  <SourceCard key={source.chunk_id} source={source} />
                ))}
              </div>
            )}
            {message.query && (
              <FeedbackButtons token={token} sessionId={message.response.session_id} query={message.query} />
            )}
          </>
        )}
      </div>
    </div>
  );
}
