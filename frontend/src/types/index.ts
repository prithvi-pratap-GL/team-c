// Chat Message Types
export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  sources?: Source[]
  feedback?: Feedback
}

export interface Source {
  documentId: string
  documentName: string
  department: string
  category: string
  chunkReference: string
  relevanceScore: number
  pageNumber?: number
}

export interface Feedback {
  id: string
  messageId: string
  isHelpful: boolean
  comment?: string
  timestamp: Date
}

// Document Types
export interface Document {
  id: string
  name: string
  department: string
  category: string
  documentType: 'pdf' | 'txt' | 'md'
  version: string
  uploadDate: Date
  size: number
  metadata?: Record<string, unknown>
}

export interface UploadProgress {
  fileName: string
  progress: number
  status: 'pending' | 'uploading' | 'success' | 'error'
  error?: string
}

// Filter Types
export interface FilterOptions {
  departments?: string[]
  categories?: string[]
  documentTypes?: string[]
  dateRange?: {
    from: Date
    to: Date
  }
}

// Chat API Types
export interface ChatRequest {
  query: string
  filters?: FilterOptions
  conversationId?: string
}

export interface ChatResponse {
  messageId: string
  response: string
  sources: Source[]
  confidence: number
  conversationId: string
}

// User/Auth Types
export interface User {
  id: string
  email: string
  name: string
  department?: string
  role: 'viewer' | 'contributor' | 'admin'
  accessibleDepartments: string[]
}

export interface AuthToken {
  accessToken: string
  refreshToken: string
  expiresIn: number
}
