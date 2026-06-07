import { useState, useRef, useEffect } from "react";
import { Source } from "../api/client";

interface SourceCardProps {
  source: Source;
  index: number;
  isExpanded: boolean;
  onToggle: () => void;
}

function scoreClass(score: number) {
  if (score >= 0.8) return "high";
  if (score >= 0.5) return "med";
  return "low";
}

export function SourceCard({ source, index, isExpanded, onToggle }: SourceCardProps) {
  const [copied, setCopied] = useState(false);
  const bodyRef = useRef<HTMLDivElement>(null);
  const innerRef = useRef<HTMLDivElement>(null);
  const pct = Math.round(source.score * 100);

  // Smooth height animation
  useEffect(() => {
    const body = bodyRef.current;
    const inner = innerRef.current;
    if (!body || !inner) return;
    if (isExpanded) {
      body.style.height = inner.scrollHeight + "px";
    } else {
      body.style.height = "0px";
    }
  }, [isExpanded]);

  function handleCopy() {
    navigator.clipboard.writeText(source.chunk_text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  const dept = source.department.replace(/_/g, " ");
  const preview = source.chunk_text.slice(0, 90) + (source.chunk_text.length > 90 ? "…" : "");

  return (
    <div className={`source-card ${isExpanded ? "expanded" : ""}`}>
      <button className="source-trigger" onClick={onToggle} type="button">
        <span className="source-chevron">
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
            <path d="M4.5 3L7.5 6L4.5 9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </span>

        <span className="source-trigger-content">
          <span className="source-doc-name">{source.doc_name}</span>
          {!isExpanded && <span className="source-snippet">{preview}</span>}
        </span>

        <span className="source-trigger-meta">
          <span className={`source-score ${scoreClass(source.score)}`}>{pct}%</span>
          <span className="source-type-badge">{dept}</span>
        </span>
      </button>

      <div className="source-body" ref={bodyRef} style={{ height: 0 }}>
        <div className="source-body-inner" ref={innerRef}>
          <p className="source-full-text">{source.chunk_text}</p>
          <div className="source-meta-row">
            <span className="source-meta-item">
              Chunk&nbsp;<strong>{source.chunk_id.slice(-6)}</strong>
            </span>
            {source.page != null && (
              <span className="source-meta-item">
                Page&nbsp;<strong>{source.page}</strong>
              </span>
            )}
            <span className="source-meta-item">
              Score&nbsp;<strong>{pct}%</strong>
            </span>
            <span className="source-meta-item">
              Dept&nbsp;<strong>{dept}</strong>
            </span>
            <button
              className={`source-copy-btn ${copied ? "copied" : ""}`}
              onClick={(e) => { e.stopPropagation(); handleCopy(); }}
              type="button"
            >
              {copied ? (
                <>
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                    <path d="M2 6L5 9L10 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                  </svg>
                  Copied
                </>
              ) : (
                <>
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                    <rect x="1" y="3" width="7" height="8" rx="1.5" stroke="currentColor" strokeWidth="1.2"/>
                    <path d="M4 3V2a1 1 0 011-1h4a1 1 0 011 1v7a1 1 0 01-1 1h-1" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
                  </svg>
                  Copy
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

/* Accordion wrapper — only one open at a time */

export function SourcesList({ sources }: { sources: Source[] }) {
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);

  function toggle(i: number) {
    setExpandedIdx(prev => prev === i ? null : i);
  }

  return (
    <div className="sources-section">
      <div className="sources-header">
        <span className="sources-label">Sources</span>
        <span className="sources-count">{sources.length}</span>
      </div>
      <div className="sources-list">
        {sources.map((source, i) => (
          <SourceCard
            key={source.chunk_id}
            source={source}
            index={i + 1}
            isExpanded={expandedIdx === i}
            onToggle={() => toggle(i)}
          />
        ))}
      </div>
    </div>
  );
}
