import { useEffect, useState } from "react";
import { api, DocumentSummary } from "../api/client";
import { DocumentTable, DocumentUpload } from "../components/DocumentUpload";

interface UploadPageProps {
  token: string;
  isAdmin: boolean;
}

export function UploadPage({ token, isAdmin }: UploadPageProps) {
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [error, setError] = useState("");

  async function loadDocuments() {
    setError("");
    try {
      const response = await api.listDocuments(token);
      setDocuments(response.documents);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load documents");
    }
  }

  useEffect(() => {
    void loadDocuments();
  }, [token]);

  return (
    <section className="upload-page">
      <div className="section-heading">
        <h2>Documents</h2>
        <p>{documents.length} visible documents</p>
      </div>
      {isAdmin && <DocumentUpload token={token} onUploaded={loadDocuments} />}
      {!isAdmin && <p className="notice">Only admin users can upload documents.</p>}
      {error && <p className="error-text">{error}</p>}
      <DocumentTable documents={documents} />
    </section>
  );
}
