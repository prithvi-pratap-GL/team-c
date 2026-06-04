import { Source } from "../api/client";

interface SourceCardProps {
  source: Source;
}

export function SourceCard({ source }: SourceCardProps) {
  return (
    <article className="source-card">
      <div className="source-topline">
        <strong>{source.doc_name}</strong>
        <span>{Math.round(source.score * 100)}%</span>
      </div>
      <p>{source.chunk_text}</p>
      <div className="source-meta">
        <span>{source.department.replace("_", " ")}</span>
        <span>{source.chunk_id}</span>
      </div>
    </article>
  );
}
