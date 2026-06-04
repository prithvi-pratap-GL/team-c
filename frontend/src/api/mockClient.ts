import { LoginResponse, ChatResponse, DocumentsResponse, IngestResponse, ChatFilters } from "./client";
import { mockLogin, mockChat, mockListDocuments, mockIngest } from "./mock";

// Simulate network delay for realistic feel
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const mockApi = {
  async login(username: string, password: string) {
    await delay(800);
    return mockLogin(username, password);
  },

  async chat(token: string, payload: { query: string; filters: ChatFilters; retrieval_mode: string; session_id?: string }) {
    await delay(1500);
    return mockChat(payload.query);
  },

  async listDocuments(token: string, filters: { department?: string; category?: string } = {}) {
    await delay(600);
    return mockListDocuments(filters.department);
  },

  async ingest(token: string, file: File, metadata: any) {
    await delay(2000);
    return mockIngest();
  },

  async feedback(token: string, payload: { session_id: string; query: string; helpful: boolean; comment?: string }) {
    await delay(500);
    return { status: "success" };
  },
};
