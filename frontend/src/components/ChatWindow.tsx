import { useState } from "react";
import { Department } from "../api/client";
import { useChat } from "../hooks/useChat";
import { FilterPanel } from "./FilterPanel";
import { MessageBubble } from "./MessageBubble";

interface ChatWindowProps {
  token: string;
  allowedDepartments: Department[];
}

// Trial Phase: Updated with new chat header design including filter modal and retrieval mode buttons
export function ChatWindow({ token, allowedDepartments }: ChatWindowProps) {
  const chat = useChat(token);
  const [showFilters, setShowFilters] = useState(false);

  return (
    <section className="chat-layout-full">
      {showFilters && (
        <div className="filter-modal-overlay" onClick={() => setShowFilters(false)}>
          <div className="filter-modal" onClick={(e) => e.stopPropagation()}>
            <div className="filter-modal-header">
              <h2>Filters</h2>
              <button
                className="filter-modal-close"
                onClick={() => setShowFilters(false)}
                type="button"
              >
                ×
              </button>
            </div>
            <FilterPanel
              filters={chat.filters}
              onFiltersChange={chat.setFilters}
              allowedDepartments={allowedDepartments}
            />
          </div>
        </div>
      )}

      <div className="chat-panel">
        <div className="chat-header">
          <div className="active-filters">
            <button
              className="filter-toggle"
              onClick={() => setShowFilters(true)}
              type="button"
            >
              <span className="filter-icon">⚙️</span> Filters
            </button>
            {chat.filters.department && (
              <span className="filter-chip">
                {chat.filters.department.replace("_", " ")}
                <button
                  className="chip-close"
                  onClick={() => chat.setFilters({ ...chat.filters, department: undefined })}
                  type="button"
                >
                  ×
                </button>
              </span>
            )}
            {chat.filters.category && (
              <span className="filter-chip">
                {chat.filters.category.replace("_", " ")}
                <button
                  className="chip-close"
                  onClick={() => chat.setFilters({ ...chat.filters, category: undefined })}
                  type="button"
                >
                  ×
                </button>
              </span>
            )}
          </div>
          <div className="retrieval-mode">
            <button
              className={`mode-btn ${chat.retrievalMode === "hybrid" ? "active" : ""}`}
              onClick={() => chat.setRetrievalMode("hybrid")}
              type="button"
            >
              Hybrid
            </button>
            <button
              className={`mode-btn ${chat.retrievalMode === "vector" ? "active" : ""}`}
              onClick={() => chat.setRetrievalMode("vector")}
              type="button"
            >
              Vector
            </button>
          </div>
        </div>

        <div className="chat-history">
          {chat.messages.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">💬</div>
              <h2>Ask across your knowledge base</h2>
              <p>Try a policy, guide, or incident query after uploading documents</p>
            </div>
          ) : (
            chat.messages.map((message) => <MessageBubble key={message.id} message={message} token={token} />)
          )}
        </div>

        {chat.error && <p className="error-text">⚠️ {chat.error}</p>}

        <form className="composer" onSubmit={chat.submit}>
          <textarea
            value={chat.query}
            onChange={(event) => chat.setQuery(event.target.value)}
            placeholder="Ask a question..."
            rows={2}
            className="chat-input"
          />
          <button className="send-button" disabled={chat.loading} type="submit">
            {chat.loading ? "⊙" : "➤"}
          </button>
        </form>
      </div>
    </section>
  );
}
