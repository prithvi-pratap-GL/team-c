import { FormEvent, useState } from "react";
import { api, Category, Department, DocumentSummary, IngestMetadata } from "../api/client";

interface DocumentUploadProps {
  token: string;
  onUploaded: () => void;
}

const departments: Department[] = ["engineering", "hr", "operations", "product_support"];
const categories: Category[] = ["policy", "guide", "faq", "incident", "release_notes"];

export function DocumentUpload({ token, onUploaded }: DocumentUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [metadata, setMetadata] = useState<IngestMetadata>({
    department: "engineering",
    category: "guide",
    version: "1.0",
    doc_date: new Date().toISOString().slice(0, 10),
    chunking_strategy: "fixed",
  });
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!file) {
      setStatus("Choose a file first");
      return;
    }

    setLoading(true);
    setStatus("");
    try {
      const response = await api.ingest(token, file, metadata);
      setStatus(`Uploaded ${response.doc_id}`);
      setFile(null);
      onUploaded();
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="upload-form" onSubmit={submit}>
      <label className="file-drop">
        <input
          accept=".txt,.pdf"
          type="file"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
        />
        <span>{file ? file.name : "Choose TXT or PDF"}</span>
      </label>

      <div className="form-grid">
        <label>
          Department
          <select
            value={metadata.department}
            onChange={(event) => setMetadata({ ...metadata, department: event.target.value as Department })}
          >
            {departments.map((department) => (
              <option key={department} value={department}>
                {department.replace("_", " ")}
              </option>
            ))}
          </select>
        </label>

        <label>
          Category
          <select
            value={metadata.category}
            onChange={(event) => setMetadata({ ...metadata, category: event.target.value as Category })}
          >
            {categories.map((category) => (
              <option key={category} value={category}>
                {category.replace("_", " ")}
              </option>
            ))}
          </select>
        </label>

        <label>
          Version
          <input value={metadata.version} onChange={(event) => setMetadata({ ...metadata, version: event.target.value })} />
        </label>

        <label>
          Document date
          <input
            type="date"
            value={metadata.doc_date}
            onChange={(event) => setMetadata({ ...metadata, doc_date: event.target.value })}
          />
        </label>
      </div>

      <div className="segmented-control">
        <button
          className={metadata.chunking_strategy === "fixed" ? "active" : ""}
          onClick={() => setMetadata({ ...metadata, chunking_strategy: "fixed" })}
          type="button"
        >
          Fixed
        </button>
        <button
          className={metadata.chunking_strategy === "semantic" ? "active" : ""}
          onClick={() => setMetadata({ ...metadata, chunking_strategy: "semantic" })}
          type="button"
        >
          Semantic
        </button>
      </div>

      <button className="primary-button" disabled={loading} type="submit">
        {loading ? "Uploading" : "Upload document"}
      </button>
      {status && <p className="status-text">{status}</p>}
    </form>
  );
}

interface DocumentTableProps {
  documents: DocumentSummary[];
}

export function DocumentTable({ documents }: DocumentTableProps) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Department</th>
            <th>Category</th>
            <th>Version</th>
            <th>Date</th>
            <th>Chunks</th>
          </tr>
        </thead>
        <tbody>
          {documents.map((document) => (
            <tr key={document.doc_id}>
              <td>{document.doc_name}</td>
              <td>{document.department.replace("_", " ")}</td>
              <td>{document.category.replace("_", " ")}</td>
              <td>{document.version}</td>
              <td>{document.doc_date}</td>
              <td>{document.chunk_count}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {documents.length === 0 && <p className="table-empty">No documents visible for this account.</p>}
    </div>
  );
}
