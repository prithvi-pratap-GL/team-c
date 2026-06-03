import { Department } from "../api/client";
import { useChat } from "../hooks/useChat";
import { FilterPanel } from "./FilterPanel";
import { MessageBubble } from "./MessageBubble";

interface ChatWindowProps {
  token: string;
  allowedDepartments: Department[];
}

export function ChatWindow({ token, allowedDepartments }: ChatWindowProps) {
  const chat = useChat(token);

  return (
    <section className="chat-layout">
      <FilterPanel
        filters={chat.filters}
        retrievalMode={chat.retrievalMode}
        onFiltersChange={chat.setFilters}
        onRetrievalModeChange={chat.setRetrievalMode}
        allowedDepartments={allowedDepartments}
      />

      <div className="chat-panel">
        <div className="chat-history">
          {chat.messages.length === 0 ? (
            <div className="empty-state">
              <h2>Ask across your approved knowledge base</h2>
              <p>Try a deployment, HR policy, support FAQ, or incident query after uploading documents.</p>
            </div>
          ) : (
            chat.messages.map((message) => <MessageBubble key={message.id} message={message} token={token} />)
          )}
        </div>

        {chat.error && <p className="error-text">{chat.error}</p>}

        <form className="composer" onSubmit={chat.submit}>
          <textarea
            value={chat.query}
            onChange={(event) => chat.setQuery(event.target.value)}
            placeholder="Ask a question..."
            rows={2}
          />
          <button className="primary-button" disabled={chat.loading} type="submit">
            {chat.loading ? "Sending" : "Send"}
          </button>
        </form>
      </div>
    </section>
  );
}
