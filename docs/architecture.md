# Architecture - Enterprise RAG Assistant

## System Overview

```
┌─────────────┐
│   User      │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────────┐
│        Frontend (React 18)            │
│  • Chat window                        │
│  • Document upload                    │
│  • Source cards (attribution)         │
│  • Feedback buttons                   │
└──────────────┬───────────────────────┘
               │ REST API / JSON
               ▼
┌──────────────────────────────────────────────────────┐
│              Backend (FastAPI)                        │
│  ┌────────────────────────────────────────────────┐  │
│  │ Auth Middleware (JWT + RBAC)                   │  │
│  │  • Validate JWT token                          │  │
│  │  • Extract role & departments_allowed          │  │
│  │  • Enforce permission checks                   │  │
│  └────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────┐  │
│  │ Routers                                        │  │
│  │  • /auth/login → JWT token                    │  │
│  │  • /chat → RAG pipeline                       │  │
│  │  • /ingest → document upload                  │  │
│  │  • /feedback → user feedback                  │  │
│  │  • /documents → list available docs           │  │
│  └────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────┐  │
│  │ RAG Pipeline (LangChain)                       │  │
│  │  • Embedder (OpenAI text-embedding-3-small)   │  │
│  │  • Retriever (vector + hybrid)                │  │
│  │  • Reranker (cross-encoder)                   │  │
│  │  • LLM Chain (gpt-4o-mini)                    │  │
│  └────────────────────────────────────────────────┘  │
└──────┬───────────────────────────────────────────────┘
       │
       ├──────────────────┬──────────────────┬──────────────┐
       ▼                  ▼                  ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ PostgreSQL   │ │   Qdrant     │ │    Redis     │ │  OpenAI API  │
│ (Metadata)   │ │   (Vectors)  │ │   (Cache)    │ │  (Embedding) │
│              │ │              │ │              │ │  (LLM)       │
│ • Users      │ │ • Collections│ │ • Query      │ └──────────────┘
│ • Documents  │ │ • Payloads   │ │   embeddings │
│ • Feedback   │ │ • Hybrid     │ │ • Results    │
│ • Access     │ │   search     │ │   (5 min TTL)│
│   rules      │ │              │ │              │
└──────────────┘ └──────────────┘ └──────────────┘
```

## Data Flow: Ingestion Path

```
Document Upload
    │
    ▼
[Parser] ← Select by file type
    │ (pypdf for PDF, direct read for TXT)
    ▼
[Content Extraction]
    │ (text, page count, metadata)
    ▼
[Chunking - DUAL PATH]
    ├─→ [Fixed Chunker] ← chunk_size=512, overlap=64
    └─→ [Semantic Chunker] ← threshold=0.85
    │
    ▼
[Embedding]
    ├─→ [Dense Embedder] ← OpenAI text-embedding-3-small (1536-dim)
    └─→ [Sparse Embedder] ← fastembed BM25
    │
    ▼
[Qdrant Upsert]
    │ (with full metadata payload)
    ▼
[PostgreSQL Update]
    │ (document record + chunk counts)
    ▼
[Upload Complete]
```

## Data Flow: Query Path

```
User Query
    │
    ▼
[Authentication]
    │ (JWT validation + role extraction)
    ▼
[Query Embedding]
    ├─→ [Redis Cache Check] ← (5 min TTL)
    └─→ [OpenAI Embedding] ← If cache miss
    │
    ▼
[RBAC Filter Construction]
    │ {"department": {"any": user.departments_allowed}}
    ▼
[Retrieval - DUAL PATH]
    ├─→ [Vector Search]
    │   • Qdrant dense similarity search
    │   • top_k=10, with metadata filter
    │
    └─→ [Hybrid Search]
        • Dense (α=0.7) + Sparse BM25 (α=0.3)
        • Reciprocal Rank Fusion (RRF)
        • top_k=10, with metadata filter
    │
    ▼
[Reranker]
    │ (cross-encoder/ms-marco-MiniLM-L-6-v2)
    │ (Re-score top-10, keep top-5)
    ▼
[Score Threshold Check]
    │ If max_score < 0.40 → return not_found (skip LLM)
    ▼
[Prompt Assembly]
    │ System: "Answer only from context..."
    │ Context: Top-5 chunks with [SOURCE N] labels
    │ User: Original query
    ▼
[LLM Generation]
    │ (gpt-4o-mini with temperature=0.7)
    ▼
[Source Attribution Extraction]
    │ (Parse [SOURCE N] references from response)
    ▼
[Response Assembly]
    │ {answer, sources, confidence, session_id}
    ▼
[Return to Frontend]
```

## Storage Layer

### PostgreSQL (Metadata Store)
**Purpose**: Relational integrity for document lifecycle, users, feedback, and RBAC rules

**Tables**:
- `users` — User accounts with roles and department assignments
- `documents` — Document metadata (name, department, category, chunk counts)
- `document_versions` — Audit trail of document changes
- `chat_sessions` — Track conversation sessions
- `feedback` — User feedback on responses
- `experiment_results` — Evaluation metrics and results
- `access_control_rules` — RBAC rule definitions

### Qdrant (Vector Database)
**Purpose**: Hybrid search with metadata filtering

**Collections**:
- `documents_fixed` — Fixed-size chunks (512 tokens, 64 overlap)
- `documents_semantic` — Semantic chunks (variable size)

**Payload per point**:
```json
{
  "chunk_text": "full chunk content",
  "chunk_id": "uuid",
  "doc_id": "uuid",
  "doc_name": "HR Policy Handbook",
  "department": "hr",
  "category": "policy",
  "version": "2.1",
  "doc_date": "2024-01-15",
  "page_number": 5,
  "chunking_strategy": "fixed|semantic",
  "char_offset": 12345
}
```

### Redis (Cache)
**Purpose**: Fast embedding and result caching

**Entries**:
- `query_embedding:{hash}` → `[1.0, -0.5, ...]` (TTL: 5 min)
- `chat_session:{session_id}` → conversation context
- `embedding_cache:{chunk_id}` → cached embeddings

## Security & Access Control

### RBAC Implementation
**Layer**: Enforced at **retrieval time** in Qdrant, not post-retrieval

**Flow**:
1. User logs in → JWT token with `departments_allowed` claim
2. `/chat` request includes token in Authorization header
3. Backend decodes JWT → extracts `departments_allowed`
4. Constructs mandatory Qdrant filter: `{"department": {"any": departments_allowed}}`
5. **Server injects filter server-side** — user cannot override
6. Qdrant returns only chunks from allowed departments
7. Frontend never sees cross-departmental data

### Authentication
- JWT (python-jose) with HS256 algorithm
- 24-hour token expiration
- Demo users: admin (all departments), alice_hr (HR only), bob_eng (engineering only), etc.

### Validation
- Pydantic models enforce schema at API boundary
- Department and category enums prevent invalid values
- Required fields validated automatically

## Performance Considerations

### Caching Strategy
- **Query embeddings**: 5-min cache in Redis (avoid duplicate API calls)
- **Retrieved chunks**: Cached in session context
- **Model inference**: No caching (stateless LLM calls)

### Batch Processing
- Embeddings: Batch up to 100 chunks per OpenAI API call
- Sparse embeddings: Generated locally (no API)

### Retrieval Optimization
- Vector: O(1) approx with HNSW indexing (Qdrant default)
- Hybrid: Dense + Sparse in parallel, fused with RRF
- Reranking: Only top-10 results (cheap cross-encoder pass)

## Hallucination Prevention

**Strategy**: Multi-layer defense

1. **System Prompt**: Explicit instructions to answer only from context
2. **Score Threshold**: Skip LLM if max retrieval score < 0.40
3. **No Context Path**: Return "not found" without LLM call if no good sources
4. **Source Attribution**: Require [SOURCE N] references in response
5. **Grounding Check** (optional): Separate verification prompt

## Scalability Notes

**Current bottlenecks** (single-instance demo):
- OpenAI API rate limits (requires key rotation or paid tier)
- Qdrant in single container (no sharding)
- PostgreSQL single instance (no replication)

**For production**:
- Qdrant cluster mode for large scale
- PostgreSQL replication + connection pooling
- Redis Sentinel for failover
- Load balancer in front of FastAPI
- Streaming responses for long-form answers
- Batch ingestion jobs for bulk documents

## Design Rationale

**Monorepo**: Shared .env, docker-compose, and contracts → single `docker-compose up` for judges

**Frozen Schemas at T+30m**: Forces alignment early, prevents late-stage integration bugs

**RBAC at Retrieval**: Prevents data leakage at the source (Qdrant filter), not after retrieval

**Dual Chunking**: Experiments show semantic preserves answers better; fixed is faster for structured data

**Hybrid Search**: BM25 (sparse) excels at exact matches (INC-2024-003); dense excels at semantic similarity

**Redis Cache**: 5-min TTL eliminates redundant embedding API calls during demo

**Cross-encoder Reranking**: Cheap 2-pass approach beats training custom ranker
