import { useState } from "react";
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
        {/* Header */}
        <div className="chat-header">
          <div className="active-filters">
            <button
              className="filter-toggle"
              onClick={() => setShowFilters(true)}
              type="button"
            >
              <span className="filter-icon">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M22 3H2l8 9.46V19l4 2v-8.54L22 3z"/>
                </svg>
              </span>
              Filters
            </button>
            {chat.filters.department && (
              <span className="filter-chip">
                {chat.filters.department.replace("_", " ")}
                <button
                  className="chip-close"
                  onClick={() => chat.setFilters({ ...chat.filters, department: undefined })}
                  type="button"
                >×</button>
              </span>
            )}
            {chat.filters.category && (
              <span className="filter-chip">
                {chat.filters.category.replace("_", " ")}
                <button
                  className="chip-close"
                  onClick={() => chat.setFilters({ ...chat.filters, category: undefined })}
                  type="button"
                >×</button>
              </span>
            )}
          </div>
          <div className="retrieval-mode">
            <button
              className={`mode-btn ${chat.retrievalMode === "hybrid" ? "active" : ""}`}
              onClick={() => chat.setRetrievalMode("hybrid")}
              type="button"
            >Hybrid</button>
            <button
              className={`mode-btn ${chat.retrievalMode === "vector" ? "active" : ""}`}
              onClick={() => chat.setRetrievalMode("vector")}
              type="button"
            >Vector</button>
          </div>
        </div>

        {/* Messages */}
        <div className="chat-history">
          {chat.messages.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">⌕</div>
              <h2>Ask your knowledge base</h2>
              <p>Query policies, guides, incident reports, and more — with source-linked answers.</p>
            </div>
          ) : (
            chat.messages.map((message) => (
              <MessageBubble key={message.id} message={message} token={token} />
            ))
          )}
          {chat.error && <p className="error-text">⚠ {chat.error}</p>}
        </div>

        {/* Composer */}
        <div className="composer-strip">
          <form className="composer" onSubmit={chat.submit}>
            <textarea
              value={chat.query}
              onChange={(e) => chat.setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  void chat.submit();
                }
              }}
              placeholder="Ask a question…"
              rows={1}
              className="chat-input"
            />
            <button className="send-button" disabled={chat.loading} type="submit">
              {chat.loading ? (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
                </svg>
              ) : (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                  <path d="M22 2L11 13M22 2L15 22l-4-9-9-4 20-7z"/>
                </svg>
              )}
            </button>
          </form>
        </div>
      </div>
    </section>
  );
}
