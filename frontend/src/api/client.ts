const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

export type Department = "engineering" | "hr" | "operations" | "product_support";
export type Category = "policy" | "guide" | "faq" | "incident" | "release_notes";
export type RetrievalMode = "vector" | "hybrid";
export type Confidence = "high" | "low" | "not_found";

export interface LoginResponse {
  access_token: string;
  token_type: "bearer";
  role: "admin" | "engineering" | "hr" | "operations" | "support";
  departments_allowed: Department[];
}

export interface ChatFilters {
  department?: Department;
  category?: Category;
  year?: number;
  doc_type?: string;
}

export interface Source {
  doc_id: string;
  doc_name: string;
  department: Department;
  chunk_text: string;
  chunk_id: string;
  score: number;
  page?: number | null;
}

export interface ChatResponse {
  answer: string;
  sources: Source[];
  retrieval_mode_used: RetrievalMode;
  confidence: Confidence;
  session_id: string;
}

export interface DocumentSummary {
  doc_id: string;
  doc_name: string;
  department: Department;
  category: Category;
  version: string;
  doc_date: string;
  chunk_count: number;
}

export interface DocumentsResponse {
  documents: DocumentSummary[];
  total: number;
  page: number;
}

export interface IngestMetadata {
  department: Department;
  category: Category;
  version: string;
  doc_date: string;
  chunking_strategy: "fixed" | "semantic";
}

export interface IngestResponse {
  job_id: string;
  status: string;
  doc_id: string;
}

async function request<T>(path: string, token: string | null, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (!(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const message = typeof data.detail === "string" ? data.detail : "Request failed";
    throw new Error(message);
  }

  return data as T;
}

export const api = {
  login(username: string, password: string) {
    return request<LoginResponse>("/auth/login", null, {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
  },

  chat(token: string, payload: { query: string; filters: ChatFilters; retrieval_mode: RetrievalMode; session_id?: string }) {
    return request<ChatResponse>("/chat", token, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  listDocuments(token: string, filters: { department?: Department; category?: Category } = {}) {
    const params = new URLSearchParams();
    if (filters.department) params.set("department", filters.department);
    if (filters.category) params.set("category", filters.category);
    const suffix = params.toString() ? `?${params.toString()}` : "";
    return request<DocumentsResponse>(`/documents${suffix}`, token);
  },

  ingest(token: string, file: File, metadata: IngestMetadata) {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("metadata", JSON.stringify(metadata));
    return request<IngestResponse>("/ingest", token, {
      method: "POST",
      body: formData,
    });
  },

  feedback(token: string, payload: { session_id: string; query: string; helpful: boolean; comment?: string }) {
    return request<{ status: string }>("/feedback", token, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
};
