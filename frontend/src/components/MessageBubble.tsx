import { ChatResponse } from "../api/client";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { FeedbackButtons } from "./FeedbackButtons";
import { SourcesList } from "./SourceCard";

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
        {isAssistant ? (
          <>
            {message.response && (
              <div className={`confidence ${message.response.confidence}`}>
                {message.response.confidence === "high" && "● "}
                {message.response.confidence === "low" && "◐ "}
                {message.response.confidence === "not_found" && "○ "}
                {message.response.confidence.replace("_", " ")}
              </div>
            )}
            <div className="assistant-answer">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.text}
              </ReactMarkdown>
            </div>
            {isAssistant && message.response && message.response.sources.length > 0 && (
              <SourcesList sources={message.response.sources} />
            )}
            {message.query && message.response && (
              <FeedbackButtons
                token={token}
                sessionId={message.response.session_id}
                query={message.query}
              />
            )}
          </>
        ) : (
          <p>{message.text}</p>
        )}
      </div>
    </div>
  );
}
