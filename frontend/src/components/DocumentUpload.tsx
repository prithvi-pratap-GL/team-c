import { FormEvent, useState } from "react";
import { api, Category, Department, DocumentSummary, IngestMetadata } from "../api/client";

interface DocumentUploadProps {
  token: string;
  onUploaded: () => void;
}

const departments: Department[] = ["engineering", "hr", "operations", "product_support"];
const categories: Category[] = ["policy", "guide", "faq", "incident", "release_notes"];

const departmentColors: Record<Department, string> = {
  engineering: "#667eea",
  hr: "#10b981",
  operations: "#f59e0b",
  product_support: "#ef4444",
};

export function DocumentUpload({ token, onUploaded }: DocumentUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [metadata, setMetadata] = useState<IngestMetadata>({
    department: "" as Department,
    category: "" as Category,
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
      setTimeout(() => setStatus(""), 5000);
      return;
    }
    if (!metadata.department) {
      setStatus("Select a department");
      setTimeout(() => setStatus(""), 5000);
      return;
    }
    if (!metadata.category) {
      setStatus("Select a category");
      setTimeout(() => setStatus(""), 5000);
      return;
    }
    if (!metadata.version.trim()) {
      setStatus("Enter a version");
      setTimeout(() => setStatus(""), 5000);
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
    <div className="document-upload-section">
      <div className="section-card">
        <div className="section-header">
          <div>
            <h2>Upload document</h2>
            <p>Add a new document to the knowledge base</p>
          </div>
        </div>

        <form className="document-form" onSubmit={submit}>
          <label className="file-drop-area">
            <input
              accept=".txt,.pdf"
              type="file"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            />
            <div className="drop-content">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2v20M2 12h20" />
              </svg>
              <p className="drop-text">Drop your file here or click to browse</p>
              <p className="drop-subtitle"><em>Supports PDF and TXT — max 50 MB</em></p>
              {file && <p className="file-name">📄 {file.name}</p>}
            </div>
          </label>

          <div className="form-fields">
            <div className="form-row">
              <label className="form-label">
                <span>Department</span>
                <select
                  value={metadata.department}
                  onChange={(event) => setMetadata({ ...metadata, department: event.target.value as Department })}
                  className="form-select"
                >
                  <option value="">Select</option>
                  {departments.map((department) => (
                    <option key={department} value={department}>
                      {department.split("_").map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(" ")}
                    </option>
                  ))}
                </select>
              </label>

              <label className="form-label">
                <span>Category</span>
                <select
                  value={metadata.category}
                  onChange={(event) => setMetadata({ ...metadata, category: event.target.value as Category })}
                  className="form-select"
                >
                  <option value="">Select</option>
                  {categories.map((category) => (
                    <option key={category} value={category}>
                      {category.split("_").map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(" ")}
                    </option>
                  ))}
                </select>
              </label>

              <label className="form-label">
                <span>Version</span>
                <input
                  type="text"
                  placeholder="e.g. 1.0"
                  value={metadata.version}
                  onChange={(event) => setMetadata({ ...metadata, version: event.target.value })}
                  className="form-input"
                />
              </label>

              <label className="form-label">
                <span>Document Date</span>
                <input
                  type="date"
                  value={metadata.doc_date}
                  onChange={(event) => setMetadata({ ...metadata, doc_date: event.target.value })}
                  className="form-input"
                />
              </label>
            </div>

            <div className="chunking-section">
              <span className="chunking-label">Chunking Strategy</span>
              <div className="chunking-buttons">
                <button
                  type="button"
                  className={`chunking-btn ${metadata.chunking_strategy === "fixed" ? "active" : ""}`}
                  onClick={() => setMetadata({ ...metadata, chunking_strategy: "fixed" })}
                >
                  Fixed
                </button>
                <button
                  type="button"
                  className={`chunking-btn ${metadata.chunking_strategy === "semantic" ? "active" : ""}`}
                  onClick={() => setMetadata({ ...metadata, chunking_strategy: "semantic" })}
                >
                  Semantic
                </button>
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || !file}
            className={`upload-button ${loading ? "uploading" : ""}`}
          >
            {loading ? "Uploading document..." : "Upload document"}
          </button>

          {status && <p className="upload-status">{status}</p>}
        </form>
      </div>
    </div>
  );
}

interface DocumentTableProps {
  documents: DocumentSummary[];
}

export function DocumentTable({ documents }: DocumentTableProps) {
  return (
    <div className="documents-section">
      <div className="documents-header">
        <div>
          <h2>Documents</h2>
          <p>All indexed documents in the knowledge base</p>
        </div>
        <div className="documents-count">{documents.length} documents</div>
      </div>

      <div className="table-wrap">
        <table className="documents-table">
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
                <td className="doc-name">{document.doc_name}</td>
                <td>
                  <span
                    className="dept-badge"
                    style={{
                      backgroundColor: departmentColors[document.department] + "20",
                      color: departmentColors[document.department],
                    }}
                  >
                    {document.department.replace("_", " ")}
                  </span>
                </td>
                <td>
                  <span className="category-badge">{document.category.replace("_", " ")}</span>
                </td>
                <td>{document.version}</td>
                <td>{document.doc_date}</td>
                <td>{document.chunk_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {documents.length === 0 && (
          <div className="table-empty">
            <p>No documents visible for this account.</p>
          </div>
        )}
      </div>
    </div>
  );
}
