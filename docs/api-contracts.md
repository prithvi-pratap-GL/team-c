# API Contracts - Enterprise RAG Assistant

**Status**: FROZEN at T+30m (Locked Sprint Contracts)

These contracts define the interface between frontend and backend. Once committed, they cannot change without team-wide approval.

## Authentication

### POST /api/v1/auth/login

**Request**:
```json
{
  "username": "bob_eng",
  "password": "eng123"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "role": "engineering",
  "departments_allowed": ["engineering"]
}
```

## Chat / Query Endpoint

### POST /api/v1/chat

**Request**:
```json
{
  "query": "How do I rollback a failed deployment?",
  "filters": {
    "department": "engineering",
    "category": "guide"
  },
  "retrieval_mode": "hybrid",
  "session_id": "session-uuid-optional"
}
```

**Response** (200 OK):
```json
{
  "answer": "To rollback a failed deployment: 1. Identify the previous stable version... [SOURCE 1]",
  "sources": [
    {
      "doc_id": "doc-123",
      "doc_name": "Deployment Guide v2.1",
      "department": "engineering",
      "chunk_text": "To rollback: use `git revert` or deploy previous version...",
      "chunk_id": "chunk-456",
      "score": 0.92,
      "page": 5
    }
  ],
  "retrieval_mode_used": "hybrid",
  "confidence": "high",
  "session_id": "session-uuid"
}
```

## Document Management

### GET /api/v1/documents

**Query Parameters**:
- `department`: (optional) engineering | hr | operations | product_support
- `category`: (optional) policy | guide | faq | incident | release_notes
- `page`: (default 1)
- `page_size`: (default 20)

**Response** (200 OK):
```json
{
  "documents": [
    {
      "doc_id": "doc-123",
      "doc_name": "HR Policy Handbook 2024",
      "department": "hr",
      "category": "policy",
      "version": "2.1",
      "doc_date": "2024-01-15",
      "chunk_count": 150
    }
  ],
  "total": 245,
  "page": 1,
  "page_size": 20
}
```

## Document Ingestion

### POST /api/v1/ingest

**Request** (multipart/form-data):
- `file`: PDF or TXT file
- `metadata`: JSON string
  ```json
  {
    "department": "engineering",
    "category": "guide",
    "version": "2.1",
    "doc_date": "2024-03-01",
    "chunking_strategy": "semantic"
  }
  ```

**Response** (202 Accepted):
```json
{
  "job_id": "job-uuid",
  "status": "processing",
  "doc_id": "doc-uuid"
}
```

### GET /api/v1/ingest/status/{job_id}

**Response** (200 OK):
```json
{
  "job_id": "job-uuid",
  "status": "processing|completed|failed",
  "progress": 65,
  "message": "Generating embeddings..."
}
```

## Feedback Endpoint

### POST /api/v1/feedback

**Request**:
```json
{
  "session_id": "session-uuid",
  "query": "How do I rollback a failed deployment?",
  "helpful": false,
  "comment": "Answer was too generic, didn't mention git revert"
}
```

**Response** (200 OK):
```json
{
  "status": "recorded"
}
```

## Authorization

All endpoints (except /auth/login) require:
```
Authorization: Bearer <access_token>
```

The backend validates the JWT and extracts:
- `username`: User identifier
- `role`: admin | engineering | hr | operations | support
- `departments_allowed`: List of departments user can access

## RBAC Enforcement

The server applies RBAC at the **retrieval layer**, not post-retrieval:
1. User requests `/chat` with valid JWT
2. Server extracts `departments_allowed` from JWT
3. Server injects Qdrant filter: `{"department": {"any": departments_allowed}}`
4. Qdrant returns only chunks from allowed departments
5. User never sees documents outside their access level

This prevents:
- HR users from seeing engineering docs
- Non-admins from seeing cross-department data
- Accidental information leakage

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Invalid credentials | Missing authorization"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": "Invalid metadata | File must be PDF or TXT"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Error message"
}
```

## Rate Limits

Not implemented in demo but should be added for production:
- /chat: 10 req/min per user
- /ingest: 5 req/min per admin
- /feedback: 100 req/min per user

## Notes

- All timestamps are ISO 8601 format
- All IDs are UUIDs (or similar unique identifiers)
- Scores are floats between 0.0 and 1.0
- Confidence levels: "high" (score > 0.7), "low" (0.4-0.7), "not_found" (< 0.4)
