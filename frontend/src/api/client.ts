import type { ChatRequest, ChatResponse, Document } from '../types'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

class APIClient {
  private token: string | null = null

  setToken(token: string) {
    this.token = token
  }

  private getHeaders(): HeadersInit {
    return {
      'Content-Type': 'application/json',
      ...(this.token && { Authorization: `Bearer ${this.token}` }),
    }
  }

  async chat(request: ChatRequest): Promise<ChatResponse> {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(request),
    })
    if (!response.ok) throw new Error(`Chat request failed: ${response.statusText}`)
    return response.json()
  }

  async uploadDocument(file: File, metadata?: Record<string, unknown>): Promise<Document> {
    const formData = new FormData()
    formData.append('file', file)
    if (metadata) {
      formData.append('metadata', JSON.stringify(metadata))
    }

    const response = await fetch(`${API_BASE_URL}/documents/upload`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${this.token}` },
      body: formData,
    })
    if (!response.ok) throw new Error(`Upload failed: ${response.statusText}`)
    return response.json()
  }

  async listDocuments(): Promise<Document[]> {
    const response = await fetch(`${API_BASE_URL}/documents`, {
      headers: this.getHeaders(),
    })
    if (!response.ok) throw new Error(`Failed to fetch documents: ${response.statusText}`)
    return response.json()
  }

  async submitFeedback(messageId: string, isHelpful: boolean, comment?: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/feedback`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ messageId, isHelpful, comment }),
    })
    if (!response.ok) throw new Error(`Feedback submission failed: ${response.statusText}`)
  }
}

export const apiClient = new APIClient()
