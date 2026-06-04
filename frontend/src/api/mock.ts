import { LoginResponse, ChatResponse, DocumentsResponse, IngestResponse, Source } from "./client";

const MOCK_USERS: Record<string, { password: string; role: LoginResponse["role"]; departments_allowed: LoginResponse["departments_allowed"] }> = {
  admin: {
    password: "admin123",
    role: "admin",
    departments_allowed: ["engineering", "hr", "operations", "product_support"],
  },
  alice_hr: {
    password: "hr123",
    role: "hr",
    departments_allowed: ["hr"],
  },
  bob_eng: {
    password: "eng123",
    role: "engineering",
    departments_allowed: ["engineering"],
  },
};

const MOCK_DOCUMENTS = [
  {
    doc_id: "doc_001",
    doc_name: "Engineering Best Practices",
    department: "engineering" as const,
    category: "guide" as const,
    version: "2.1",
    doc_date: "2024-01-15",
    chunk_count: 12,
  },
  {
    doc_id: "doc_002",
    doc_name: "HR Onboarding Process",
    department: "hr" as const,
    category: "guide" as const,
    version: "1.0",
    doc_date: "2024-02-01",
    chunk_count: 8,
  },
  {
    doc_id: "doc_003",
    doc_name: "Company Policy FAQ",
    department: "operations" as const,
    category: "faq" as const,
    version: "3.2",
    doc_date: "2024-01-20",
    chunk_count: 15,
  },
];

const MOCK_SOURCES: Source[] = [
  {
    doc_id: "doc_001",
    doc_name: "Engineering Best Practices",
    department: "engineering",
    chunk_text: "Code reviews should be completed within 24 hours. All pull requests must have at least 2 approvals.",
    chunk_id: "chunk_001_1",
    score: 0.95,
    page: 1,
  },
  {
    doc_id: "doc_002",
    doc_name: "HR Onboarding Process",
    department: "hr",
    chunk_text: "New employees receive a welcome packet on day one. Orientation runs for the first week.",
    chunk_id: "chunk_002_1",
    score: 0.87,
    page: 2,
  },
];

export function mockLogin(username: string, password: string): LoginResponse {
  const user = MOCK_USERS[username];
  if (!user || user.password !== password) {
    throw new Error("Invalid username or password");
  }
  return {
    access_token: `mock_token_${username}_${Date.now()}`,
    token_type: "bearer",
    role: user.role,
    departments_allowed: user.departments_allowed,
  };
}

export function mockChat(query: string): ChatResponse {
  return {
    answer: `Mock response to your query: "${query}". This is a simulated response from the backend. In a real scenario, this would be powered by your RAG system.`,
    sources: MOCK_SOURCES,
    retrieval_mode_used: "hybrid",
    confidence: "high",
    session_id: `session_${Date.now()}`,
  };
}

export function mockListDocuments(department?: string): DocumentsResponse {
  const filtered = department
    ? MOCK_DOCUMENTS.filter((doc) => doc.department === department)
    : MOCK_DOCUMENTS;

  return {
    documents: filtered,
    total: filtered.length,
    page: 1,
  };
}

export function mockIngest(): IngestResponse {
  return {
    job_id: `job_${Date.now()}`,
    status: "pending",
    doc_id: `doc_${Date.now()}`,
  };
}
