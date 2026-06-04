# RAG Challenge
# Enterprise RAG Assistant

A production-style full-stack AI assistant that answers questions from enterprise documents — policies, guides, FAQs, incident reports, and release notes — across multiple departments, with access control enforced at the retrieval layer.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Repository Structure](#repository-structure)
- [File-by-File Reference](#file-by-file-reference)
  - [Backend — App Layer](#backend--app-layer)
  - [Backend — RAG: Ingestion](#backend--rag-ingestion)
  - [Backend — RAG: Retrieval](#backend--rag-retrieval)
  - [Backend — RAG: Generation](#backend--rag-generation)
  - [Frontend](#frontend)
- [Data Model](#data-model)
- [Complete Data & Request Flow](#complete-data--request-flow)
  - [Ingestion Flow](#ingestion-flow)
  - [Chat / Query Flow](#chat--query-flow)
  - [Authentication Flow](#authentication-flow)
- [API Reference](#api-reference)
- [RBAC and Access Control](#rbac-and-access-control)
- [Chunking Strategies Explained](#chunking-strategies-explained)
- [Retrieval Pipeline Explained](#retrieval-pipeline-explained)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Running the App](#running-the-app)
- [Mock Mode (Frontend-only dev)](#mock-mode-frontend-only-dev)
- [Demo Accounts](#demo-accounts)
- [Known Issues and TODOs](#known-issues-and-todos)

---

## Project Overview

### What it does

Users log in with a role-scoped JWT, then ask questions in natural language. The system retrieves relevant document chunks from Qdrant Cloud, reranks them with a cross-encoder model, builds a context-injected prompt, and calls Groq's LLM (`llama-3.3-70b-versatile`) to generate an answer. Every response includes source attribution — the exact document name and chunk the answer came from.

### Departments and document types supported

| Department | Enum value |
|---|---|
| Engineering | `engineering` |
| Human Resources | `hr` |
| Operations | `operations` |
| Product Support | `product_support` |

| Document category | Enum value |
|---|---|
| Policy | `policy` |
| Guide | `guide` |
| FAQ | `faq` |
| Incident Report | `incident` |
| Release Notes | `release_notes` |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                          BROWSER (React SPA)                         │
│                                                                      │
│  LoginForm → JWT stored in localStorage                              │
│  ChatPage  → ChatWindow → useChat hook → api/client.ts               │
│  UploadPage → DocumentUpload + DocumentTable                         │
│  FilterPanel → department / category / retrieval mode toggles        │
│  SourceCard  → shows chunk_text + doc_name per result                │
│  FeedbackButtons → thumbs up/down per response                       │
└────────────────────────────┬─────────────────────────────────────────┘
                             │  REST / JSON  (VITE_API_BASE_URL)
                             │  Authorization: Bearer <jwt>
┌────────────────────────────▼─────────────────────────────────────────┐
│                    FASTAPI BACKEND  (port 8000)                      │
│                                                                      │
│  main.py ── startup: create_tables() + seed_demo_users()            │
│                                                                      │
│  Routers:                                                            │
│    /api/v1/auth/login      → auth_service.authenticate_user()       │
│    /api/v1/chat            → HybridRetriever → PromptBuilder        │
│                               → GroqClientService → ChatResponse    │
│    /api/v1/ingest          → IngestPipeline → Qdrant + SQLite       │
│    /api/v1/documents       → document_service.list_documents()      │
│    /api/v1/feedback        → feedback_service.record_feedback()     │
│                                                                      │
│  Middleware:                                                         │
│    rbac.py → JWT decode → TokenUser → department allow-list         │
└────┬───────────────────────────────────────────────┬────────────────┘
     │                                               │
     │  IngestPipeline                               │  HybridRetriever
     ▼                                               ▼
┌─────────────────────────┐             ┌────────────────────────────┐
│   RAG: INGESTION        │             │   RAG: RETRIEVAL           │
│                         │             │                            │
│  PDFParser / TxtParser  │             │  VectorRetriever           │
│  MetadataProcessor      │             │    → Embedder.embed_query  │
│  FixedChunker           │             │    → qdrant.query_points   │
│  AdvancedChunker        │             │  Reranker                  │
│  Embedder               │             │    → CrossEncoder.predict  │
│  QdrantClientManager    │             │  MetadataFilterBuilder     │
│    → qdrant.upsert()    │             │    (built, not yet wired)  │
└──────────┬──────────────┘             └────────────┬───────────────┘
           │                                         │
           ▼                                         ▼
┌──────────────────────┐             ┌───────────────────────────────┐
│   RAG: GENERATION    │             │   STORAGE                     │
│                      │             │                               │
│  PromptBuilder       │             │  Qdrant Cloud                 │
│  GroqClientService   │             │    collection: enterprise_docs│
│    llama-3.3-70b     │             │    vectors: 768-dim COSINE    │
└──────────────────────┘             │    payload: chunk + metadata  │
                                     │                               │
                                     │  SQLite  (rag_backend.db)     │
                                     │    users, documents,          │
                                     │    chunks, feedback,          │
                                     │    chat_logs                  │
                                     └───────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| Frontend | React 18, Vite 6, TypeScript | No UI framework — raw CSS in `styles.css` |
| Backend | FastAPI, Python 3.11, Uvicorn | Async-native, auto OpenAPI at `/docs` |
| Auth | python-jose (JWT), passlib pbkdf2_sha256 | Role + department claims in token |
| ORM / DB | SQLAlchemy, SQLite | Single `.db` file, swap URL for Postgres |
| Vector DB | Qdrant Cloud | 768-dim COSINE collection `enterprise_docs` |
| Embedding | `BAAI/bge-base-en-v1.5` via sentence-transformers | Local model, 768-dim, free |
| LLM | Groq `llama-3.3-70b-versatile` | Called via `groq` Python SDK |
| Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Local cross-encoder, ~86MB download |
| Chunking | LangChain `RecursiveCharacterTextSplitter` | Used for both fixed and advanced chunker |
| PDF Parsing | `pypdf` | Text-layer extraction, page-by-page |

---

## Repository Structure

```
enterprise-rag/
│
├── app/                              # FastAPI application root
│   ├── config.py                     # Settings, env vars, lru_cache
│   ├── main.py                       # App factory, startup hooks, CORS
│   │
│   ├── middleware/
│   │   └── rbac.py                   # JWT decode, role enforcement, dept filter
│   │
│   ├── models/
│   │   ├── schemas.py                # All Pydantic I/O contracts (shared source of truth)
│   │   └── db_models.py              # SQLAlchemy ORM: User, Document, Chunk, Feedback, ChatLog
│   │
│   ├── routers/
│   │   ├── auth.py                   # POST /auth/login
│   │   ├── chat.py                   # POST /chat
│   │   ├── ingest.py                 # POST /ingest, GET /documents
│   │   └── feedback.py               # POST /feedback
│   │
│   ├── services/
│   │   ├── auth_service.py           # Password hashing, JWT creation, user seed
│   │   ├── document_service.py       # Ingest orchestration, document listing
│   │   └── feedback_service.py       # Feedback persistence
│   │
│   └── rag/                          # Self-contained RAG package
│       ├── ingestion/
│       │   ├── parsers/
│       │   │   ├── pdf_parser.py     # pypdf page-by-page text extraction
│       │   │   └── txt_parser.py     # UTF-8 plain text reader
│       │   ├── chunkers/
│       │   │   ├── fixed_chunker.py  # 512 chars, 64 overlap
│       │   │   └── advanced_chunker.py # Paragraph/sentence-aware splits
│       │   ├── embedder.py           # BAAI/bge-base-en-v1.5 singleton
│       │   ├── metadata_processor.py # Validates + generates doc_id UUID
│       │   ├── qdrant_client_manager.py # Qdrant Cloud singleton, collection init
│       │   └── ingest_pipeline.py    # Orchestrates parse→chunk→embed→upsert
│       │
│       ├── retrieval/
│       │   ├── vector_retriever.py   # Dense cosine search via Qdrant
│       │   ├── hybrid_retriever.py   # Vector + optional rerank orchestrator
│       │   ├── rerankers.py          # CrossEncoder singleton reranker
│       │   └── metadata_filter.py    # Qdrant filter builders (dept, category, combined)
│       │
│       ├── generation/
│       │   ├── prompt_builder.py     # Context formatter + system/user prompt assembly
│       │   └── groq_client.py        # Groq SDK wrapper, llama-3.3-70b
│       │
│       ├── example_usage.py          # Standalone pipeline examples (not wired to API)
│       └── integration_test.py       # End-to-end integration test script
│
├── frontend/
│   ├── index.html
│   ├── vite.config.ts                # Vite on port 5173
│   ├── tsconfig.json
│   ├── package.json
│   └── src/
│       ├── main.tsx                  # App root, auth state, nav tabs, mock import
│       ├── styles.css                # All styles (no Tailwind, raw CSS)
│       ├── api/
│       │   ├── client.ts             # Typed fetch wrapper for all endpoints
│       │   ├── mock.ts               # In-memory mock data + handlers
│       │   ├── mockClient.ts         # Mock client interface
│       │   └── mockSetup.ts          # window.fetch interceptor (dev mode)
│       ├── components/
│       │   ├── ChatWindow.tsx        # Chat UI + form, consumes useChat
│       │   ├── MessageBubble.tsx     # Single message rendering
│       │   ├── SourceCard.tsx        # Source attribution display
│       │   ├── FilterPanel.tsx       # Department / category / mode selects
│       │   ├── DocumentUpload.tsx    # Upload form + document table
│       │   ├── FeedbackButtons.tsx   # 👍 / 👎 per assistant message
│       │   └── LoginForm.tsx         # Username/password form
│       ├── hooks/
│       │   └── useChat.ts            # All chat state: messages, submit, session_id
│       └── pages/
│           ├── ChatPage.tsx          # Wraps ChatWindow, receives token + departments
│           └── UploadPage.tsx        # Manages document list, conditionally shows upload
│
└── rag_backend.db                    # SQLite database (auto-created on first startup)
```

---

## File-by-File Reference

### Backend — App Layer

#### `app/config.py`
Defines the `Settings` Pydantic model with all configuration values and their defaults. Uses `@lru_cache` so the settings object is constructed exactly once per process. Reads from environment variables via `os.getenv`, falling back to safe defaults. Key values:

- `database_url` — SQLite path (`sqlite:///./rag_backend.db`)
- `secret_key` — JWT signing secret (must be changed in production)
- `chunk_size = 1200`, `chunk_overlap = 150` — config exists but the chunkers currently use their own hardcoded values (512/64). These are reserved for future wiring.
- `min_retrieval_score = 0.08` — threshold defined but not yet enforced in the chat router (another known TODO).
- `max_sources = 5` — passed as `top_k` to the retriever.

#### `app/main.py`
Creates the FastAPI `app` instance, registers CORS middleware (allows `localhost:5173` and `localhost:3000`), mounts all four routers under `/api/v1`, and runs two startup tasks: `create_tables()` (idempotent SQLAlchemy table creation) and `seed_demo_users()` (inserts hardcoded demo users if they don't exist). The root `GET /` returns a health check with timestamp.

#### `app/middleware/rbac.py`
Three FastAPI dependency functions that every protected route uses:

- `get_current_user(token)` — decodes the JWT, extracts `sub`, `role`, and `departments_allowed`, returns a `TokenUser`. Raises `401` on any failure.
- `require_admin(current_user)` — calls `get_current_user`, then raises `403` unless role is `admin`. Used by the ingest endpoint.
- `allowed_departments(current_user, requested)` — if `requested` is `None`, returns the user's full department list. If `requested` is specified but not in the user's list, raises `403`. Returns the validated department scope for every retrieval call.

#### `app/models/schemas.py`
The single source of truth for all request and response shapes, shared between backend and frontend (the frontend `api/client.ts` manually mirrors these types). Key enums:

- `Department` — `engineering`, `hr`, `operations`, `product_support`
- `Category` — `policy`, `guide`, `faq`, `incident`, `release_notes`
- `ChunkingStrategy` — `fixed`, `semantic` (note: backend calls this `advanced` internally — a naming mismatch)
- `RetrievalMode` — `vector`, `hybrid`
- `Confidence` — `high`, `low`, `not_found`
- `Role` — `admin`, `engineering`, `hr`, `operations`, `support`

#### `app/models/db_models.py`
SQLAlchemy ORM with five tables:

| Table | Purpose |
|---|---|
| `users` | Auth: username, hashed password, role, comma-separated departments |
| `documents` | Document registry: name, dept, category, version, chunk count, who uploaded |
| `chunks` | Chunk text + offset stored locally (separate from Qdrant vectors) |
| `feedback` | Helpful/not helpful per session + query |
| `chat_logs` | Full audit log: username, query, answer, confidence, top vector score |

`get_db()` is a FastAPI dependency that yields a SQLAlchemy session and ensures it closes even on error. `create_tables()` calls `Base.metadata.create_all()`.

#### `app/routers/auth.py`
Single route: `POST /api/v1/auth/login`. Accepts `LoginRequest`, calls `authenticate_user()`, creates a JWT via `create_access_token()`, returns `LoginResponse` with the token, role, and the user's allowed departments as a list.

#### `app/routers/chat.py`
`POST /api/v1/chat` — the core endpoint. Flow:
1. Generates or reuses `session_id`
2. Calls `allowed_departments()` to scope retrieval to the user's access
3. Instantiates `HybridRetriever` and calls `.retrieve(query, top_k)`
4. If no results → returns `not_found` response without calling the LLM
5. Builds prompts via `PromptBuilder.build_prompt()`
6. Calls `GroqClientService().generate()` to get the answer
7. Maps retrieval results to `Source` objects (chunk text truncated to 200 chars for the response)
8. Sets confidence to `high` if `top_score >= 0.5`, else `low`
9. Persists the full exchange to `chat_logs`

**Known TODO in this file:** `MetadataFilterBuilder` is imported and department scoping is resolved, but the filter is not yet passed to `HybridRetriever.retrieve()`. The `TODO` comment in the code marks this gap.

#### `app/routers/ingest.py`
Two routes:
- `POST /api/v1/ingest` — admin only. Reads the uploaded file bytes, parses the `metadata` form field as JSON, calls `create_document()` which runs the full ingestion pipeline and persists metadata to SQLite.
- `GET /api/v1/documents` — any authenticated user. Filters by the user's allowed departments (RBAC enforced), optional category filter, paginated.

#### `app/routers/feedback.py`
`POST /api/v1/feedback` — requires authentication. Calls `record_feedback()` and returns `{ "status": "recorded" }`.

#### `app/services/auth_service.py`
Handles password hashing (`pbkdf2_sha256` via passlib), JWT creation (HS256, 60-minute expiry by default), and the `seed_demo_users()` function. `ROLE_DEPARTMENTS` is the authoritative mapping from role to allowed departments. `DEMO_USERS` is the hardcoded credential dict used at startup.

#### `app/services/document_service.py`
`create_document()` is the ingest orchestrator called by the ingest router. It:
1. Saves the uploaded bytes to a temp file
2. Calls `IngestPipeline.ingest_document()` with the chunking strategy
3. Creates a `Document` ORM record in SQLite
4. Cleans up the temp file in a `finally` block

`list_documents()` queries `documents` table filtered by departments and optional category, with offset/limit pagination.

The `search_chunks()` function at the bottom is a deprecated shim — it raises `NotImplementedError` pointing to `HybridRetriever`. It will be removed.

#### `app/services/feedback_service.py`
One function: `record_feedback()` — creates a `Feedback` ORM record and commits it.

---

### Backend — RAG: Ingestion

#### `app/rag/ingestion/parsers/pdf_parser.py`
`PDFParser.parse(file_path)` — static method. Uses `pypdf.PdfReader` to iterate all pages and join their extracted text with `\n`. Returns:
```python
{ "text": str, "document_type": "pdf", "metadata": { "filename": str, "page_count": int } }
```
Raises `FileNotFoundError` or `ValueError` on bad input. Logs a warning if no text is extracted (e.g. a scanned PDF with no text layer).

#### `app/rag/ingestion/parsers/txt_parser.py`
`TxtParser.parse(file_path)` — static method. Opens and reads the file as UTF-8. Returns:
```python
{ "text": str, "document_type": "txt", "metadata": { "filename": str } }
```
Raises `ValueError` on `UnicodeDecodeError`.

#### `app/rag/ingestion/chunkers/fixed_chunker.py`
`FixedChunker.chunk(text)` — uses LangChain's `RecursiveCharacterTextSplitter` with `chunk_size=512`, `chunk_overlap=64`. Returns a list of `{ "chunk_id": UUID, "chunk_text": str }` dicts. Character-based splits, not token-based.

#### `app/rag/ingestion/chunkers/advanced_chunker.py`
`AdvancedChunker.chunk(text)` — same `RecursiveCharacterTextSplitter` parameters (512/64) but with explicit `separators = ["\n\n", "\n", ". ", " "]`. This means it tries to break at paragraph boundaries first, then newlines, then sentence ends, before falling back to spaces. Produces more semantically coherent chunks than fixed splitting on documents with clear structure.

> **Note:** The frontend calls this strategy `"semantic"` in the `IngestMetadata` schema, but the backend pipeline maps `"semantic"` → `AdvancedChunker` internally. The naming is slightly inconsistent; both refer to the same class.

#### `app/rag/ingestion/embedder.py`
Singleton `Embedder` class. Loads `BAAI/bge-base-en-v1.5` from sentence-transformers on first instantiation (cached across all requests). Provides:
- `embed_chunks(texts, batch_size=32)` → `List[List[float]]` (768-dim each)
- `embed_query(query)` → `List[float]` (single 768-dim vector)
- `get_dimension()` → `768`

The model is ~440MB and downloads automatically on first use from HuggingFace.

#### `app/rag/ingestion/metadata_processor.py`
`MetadataProcessor.validate_and_process(metadata)` — validates required fields (`department`, `category`, `version`), normalises all string values to lowercase and stripped, handles ISO date parsing gracefully, and generates a UUID for `doc_id`. Returns the enriched metadata dict.

#### `app/rag/ingestion/qdrant_client_manager.py`
Singleton `QdrantClientManager`. On first instantiation reads `QDRANT_URL` and `QDRANT_API_KEY` from environment and creates a `QdrantClient` pointed at Qdrant Cloud. Key constants:
- `COLLECTION_NAME = "enterprise_docs"`
- `VECTOR_SIZE = 768`
- `DISTANCE_METRIC = Distance.COSINE`

`create_collection()` checks if the collection exists before creating it — idempotent. `health_check()` calls `get_collections()` as a connectivity test.

#### `app/rag/ingestion/ingest_pipeline.py`
`IngestPipeline.ingest_document(file_path, metadata, chunking_strategy)` — the main orchestrator. Step by step:
1. Detect extension → route to `PDFParser` or `TxtParser`
2. Call `MetadataProcessor.validate_and_process()` to get `doc_id`
3. Select `FixedChunker` or `AdvancedChunker` based on `chunking_strategy`
4. Call `embedder.embed_chunks()` on all chunk texts
5. Build `PointStruct` objects with full payload (chunk text + all metadata fields)
6. Call `qdrant.upsert()` on the `enterprise_docs` collection

Point IDs are computed as `hash(f"{doc_id}_{chunk_id}") & 0x7FFFFFFF` — a deterministic integer from the UUID combination. Returns `{ doc_id, chunks_created, chunking_strategy, status }`.

---

### Backend — RAG: Retrieval

#### `app/rag/retrieval/vector_retriever.py`
`VectorRetriever.retrieve(query, top_k=10)` — embeds the query using the singleton `Embedder`, then calls `qdrant.query_points()` with the dense vector. Returns a list of result dicts:
```python
{
  "score": float,           # cosine similarity
  "chunk_text": str,
  "metadata": {
    "chunk_id", "doc_id", "doc_name", "department",
    "category", "version", "doc_date",
    "document_type", "chunking_strategy"
  }
}
```

#### `app/rag/retrieval/hybrid_retriever.py`
`HybridRetriever.retrieve(query, top_k=10, rerank=True, rerank_top_k=None)` — currently delegates to `VectorRetriever` for retrieval, then optionally applies cross-encoder reranking. The "hybrid" in the name anticipates future BM25 fusion (noted in docstrings as "designed to accommodate future BM25 fusion"). Right now: vector search + reranking.

If `rerank=True` (default), passes all vector results to `Reranker.rerank()` and returns the re-sorted top-k.

#### `app/rag/retrieval/rerankers.py`
Singleton `Reranker` class. Loads `cross-encoder/ms-marco-MiniLM-L-6-v2` on first use (~86MB). `rerank(query, results, top_k=5)`:
1. Builds `[query, chunk_text]` pairs for every result
2. Calls `CrossEncoder.predict(pairs)` to get relevance scores
3. Adds `rerank_score` to each result dict
4. Sorts descending by `rerank_score`
5. Returns top-k

Results preserve the original dict schema plus the added `rerank_score` field.

#### `app/rag/retrieval/metadata_filter.py`
`MetadataFilterBuilder` with three static methods:
- `department_filter(departments)` → Qdrant `Filter` with `MatchAny` on the `department` payload field
- `category_filter(categories)` → same for `category`
- `combined_filter(departments, categories)` → AND-s both conditions into one `Filter.must` list

**These filters are fully implemented but not yet wired into `HybridRetriever` or `VectorRetriever`.** They are constructed in `chat.py` but the retriever `retrieve()` call doesn't accept a `filter` argument yet. This is the primary outstanding integration task.

---

### Backend — RAG: Generation

#### `app/rag/generation/groq_client.py`
`GroqClientService` wraps the `groq` Python SDK. Default model: `llama-3.3-70b-versatile`. `generate(system_prompt, user_prompt, temperature=0.2, max_tokens=1024)` calls `client.chat.completions.create()` and returns the response string. Temperature is kept low (0.2) for deterministic, factual answers. Raises `ValueError` on empty inputs or out-of-range temperature.

#### `app/rag/generation/prompt_builder.py`
`PromptBuilder` with two static methods:

`build_context(retrieval_results)` — formats the retrieved chunks into a numbered context block:
```
[Document 1: HR Leave Policy v2.1 (confidence: 0.91)]
Annual leave entitlement is 20 days per calendar year...

[Document 2: ...]
```

`build_prompt(query, retrieval_results)` — injects the context into the system prompt template and returns `(system_prompt, user_prompt)`. The system prompt explicitly instructs the model:
- Answer ONLY from provided context
- Do NOT hallucinate or speculate
- If not found, respond: `"I cannot find reliable information in the knowledge base."`
- Cite document names from context

---

### Frontend

#### `src/main.tsx`
The root component. Manages global auth state (`token`, `profile`) in both `useState` and `localStorage`. Renders `LoginForm` if unauthenticated. After login, shows a `topbar`, tab `nav` (Chat / Documents), and either `ChatPage` or `UploadPage`. The `logout` function clears both state and localStorage with a 1-second animation delay.

**Important:** Line 3 imports `"./api/mockSetup"` — this activates the mock API interceptor. Remove or comment this line to switch to the real backend.

#### `src/api/client.ts`
Typed fetch wrapper. All API types (`LoginResponse`, `ChatResponse`, `Source`, `DocumentSummary`, etc.) are declared here. The `request<T>()` function sets `Content-Type: application/json` for non-FormData bodies, attaches the Bearer token, and throws a descriptive error if the response is not `ok`. Exports an `api` object with five methods: `login`, `chat`, `listDocuments`, `ingest`, `feedback`.

#### `src/api/mock.ts` + `src/api/mockSetup.ts`
The mock layer for frontend development without a running backend. `mockSetup.ts` replaces `window.fetch` with an interceptor that matches URL patterns (`/auth/login`, `/chat`, `/documents`, `/ingest`, `/feedback`) and returns in-memory responses with simulated delays. `mock.ts` defines `MOCK_USERS`, `MOCK_DOCUMENTS`, and `MOCK_SOURCES` and exports handler functions.

Mock users: `admin/admin123`, `alice_hr/hr123`, `bob_eng/eng123`.

#### `src/hooks/useChat.ts`
Centralises all chat state. Manages: `messages`, `query`, `filters`, `retrievalMode`, `sessionId`, `loading`, `error`. The `submit()` function appends the user message immediately (optimistic UI), calls `api.chat()`, then appends the assistant response. `sessionId` is threaded from response to request to maintain conversation context.

#### `src/components/ChatWindow.tsx`
Renders the message history and the input form. Uses `useChat` hook. Passes `allowedDepartments` down to `FilterPanel` to limit the selectable departments to those the user actually has access to.

#### `src/components/MessageBubble.tsx`
Renders a single chat message. User messages are styled differently from assistant messages. Assistant messages include `SourceCard` and `FeedbackButtons`.

#### `src/components/SourceCard.tsx`
Displays a single source attribution: document name, department, chunk score, and the first 200 chars of `chunk_text`.

#### `src/components/FilterPanel.tsx`
Dropdowns for department filter (restricted to user's allowed departments), category filter, and retrieval mode toggle (vector / hybrid). Changes propagate back to `useChat` via `setFilters` / `setRetrievalMode`.

#### `src/components/DocumentUpload.tsx`
Contains both the upload form (`DocumentUpload`) and the read-only document table (`DocumentTable`). The form has inputs for all `IngestMetadata` fields and submits via `api.ingest()`. Only rendered when `isAdmin` is true.

#### `src/components/FeedbackButtons.tsx`
Thumbs-up / thumbs-down buttons that call `api.feedback()` with the session ID, query, and `helpful: true/false`. Disables after submission.

#### `src/components/LoginForm.tsx`
Username and password form that calls `api.login()`. On success, calls the `onLogin(token, profile)` prop function provided by `main.tsx`.

---

## Data Model

### SQLite Tables

```
users
  id, username (unique), password_hash (pbkdf2_sha256),
  role (string), departments_allowed (comma-separated string), created_at

documents
  id, doc_id (UUID, unique), doc_name, department, category,
  version, doc_date, chunking_strategy, file_type, file_size,
  chunk_count, uploaded_by, created_at

chunks
  id, chunk_id (unique), doc_id (FK → documents.doc_id),
  chunk_text, page, char_offset

feedback
  id, session_id, query, helpful (bool), comment, created_at

chat_logs
  id, session_id, username, query, answer, confidence,
  top_score (float), created_at
```

### Qdrant Collection: `enterprise_docs`

```
Vector:  768-dim float, COSINE distance

Payload per point:
  chunk_id         (string, UUID)
  doc_id           (string, UUID)
  doc_name         (string)
  department       (string: engineering | hr | operations | product_support)
  category         (string: policy | guide | faq | incident | release_notes)
  version          (string)
  doc_date         (ISO string or null)
  document_type    (string: pdf | txt)
  chunk_text       (full chunk string)
  chunking_strategy (string: fixed | advanced)
```

---

## Complete Data & Request Flow

### Ingestion Flow

```
POST /api/v1/ingest
  multipart: file + metadata JSON

1. rbac.require_admin()
   └── JWT decode → role must be "admin" → else 403

2. IngestMetadata.parse_obj(json.loads(metadata))
   └── Pydantic validation: department enum, category enum, version non-empty

3. document_service.create_document()
   ├── Write bytes to temp_<uuid>_<filename>
   │
   ├── IngestPipeline.ingest_document(temp_path, metadata_dict, chunking_strategy)
   │   ├── PDFParser.parse() or TxtParser.parse()
   │   │   └── Returns { text, document_type, metadata: { filename, page_count? } }
   │   │
   │   ├── MetadataProcessor.validate_and_process()
   │   │   └── Returns { doc_id: UUID, department, category, version, date, ... }
   │   │
   │   ├── FixedChunker.chunk(text) or AdvancedChunker.chunk(text)
   │   │   └── Returns [{ chunk_id: UUID, chunk_text }]
   │   │
   │   ├── Embedder.embed_chunks(chunk_texts)
   │   │   └── Returns [[float x 768], ...]
   │   │
   │   └── QdrantClientManager.get_client().upsert(enterprise_docs, [PointStruct...])
   │       └── Each point: id=hash, vector=embedding, payload=full metadata
   │
   ├── SQLite: INSERT INTO documents (doc_id, doc_name, department, ..., chunk_count)
   │
   └── DELETE temp file

4. Return IngestResponse { job_id, doc_id, status: "processing" }
```

### Chat / Query Flow

```
POST /api/v1/chat
  JSON: { query, filters, retrieval_mode, session_id? }
  Header: Authorization: Bearer <jwt>

1. get_current_user()
   └── JWT decode → TokenUser { username, role, departments_allowed }

2. allowed_departments(current_user, filters.department)
   └── Returns scoped department list (user's access ∩ requested)

3. HybridRetriever().retrieve(query, top_k=5)
   │
   ├── VectorRetriever.retrieve(query, top_k=5)
   │   ├── Embedder.embed_query(query)   → [float x 768]
   │   └── qdrant.query_points(enterprise_docs, query_vector, limit=5)
   │       └── Returns scored points with payloads
   │
   └── Reranker.rerank(query, vector_results, top_k=5)
       ├── CrossEncoder.predict([[query, chunk_text], ...])
       ├── Add rerank_score to each result
       └── Sort descending, return top-k

4. If no results:
   └── Return ChatResponse { answer: "not found message", confidence: not_found }

5. PromptBuilder.build_prompt(query, results)
   ├── build_context() → "[Document 1: name (confidence: X.XX)]\n<chunk_text>\n..."
   └── Returns (system_prompt_with_context, user_prompt)

6. GroqClientService().generate(system_prompt, user_prompt)
   └── groq.chat.completions.create(llama-3.3-70b, temp=0.2) → answer string

7. Build Source list from results (chunk_text truncated to 200 chars)

8. confidence = "high" if top_score >= 0.5 else "low"

9. ChatLog INSERT (session_id, username, query, answer, confidence, top_score)

10. Return ChatResponse { answer, sources, retrieval_mode_used, confidence, session_id }
```

### Authentication Flow

```
POST /api/v1/auth/login
  { username, password }

1. auth_service.authenticate_user(db, username, password)
   └── SELECT FROM users WHERE username = ?
   └── pbkdf2_sha256 verify(plain, hash)
   └── Returns User ORM or None

2. create_access_token(user)
   └── JWT payload: { sub: username, role, departments_allowed: [...], exp }
   └── Signed with SECRET_KEY using HS256

3. Return LoginResponse { access_token, token_type, role, departments_allowed }

Frontend stores token + profile in localStorage.
All subsequent requests send: Authorization: Bearer <token>
```

---

## API Reference

Interactive docs available at `http://localhost:8000/docs` when the backend is running.

### `POST /api/v1/auth/login`
```json
Request:  { "username": "bob_eng", "password": "eng123" }
Response: { "access_token": "<jwt>", "token_type": "bearer",
            "role": "engineering", "departments_allowed": ["engineering"] }
```

### `POST /api/v1/ingest` *(admin only)*
```
Content-Type: multipart/form-data
  file:     <PDF or TXT file>
  metadata: '{"department":"hr","category":"policy","version":"1.0",
              "doc_date":"2024-06-01","chunking_strategy":"fixed"}'

Response 202:
  { "job_id": "<uuid>", "status": "processing", "doc_id": "<uuid>" }
```

### `POST /api/v1/chat`
```json
Request:
{
  "query": "What is the annual leave policy?",
  "filters": { "department": "hr", "category": "policy" },
  "retrieval_mode": "hybrid",
  "session_id": "optional-existing-session-id"
}

Response:
{
  "answer": "Employees are entitled to...",
  "sources": [
    {
      "doc_id": "...", "doc_name": "HR Leave Policy v1.0",
      "department": "hr", "chunk_text": "...(200 chars)...",
      "chunk_id": "...", "score": 0.89, "page": null
    }
  ],
  "retrieval_mode_used": "hybrid",
  "confidence": "high",
  "session_id": "..."
}
```

### `GET /api/v1/documents`
```
Query params: department?, category?, page=1, page_size=20
Response: { "documents": [...], "total": 42, "page": 1 }
```

### `POST /api/v1/feedback`
```json
Request:  { "session_id": "...", "query": "...", "helpful": true, "comment": "Good answer" }
Response: { "status": "recorded" }
```

---

## RBAC and Access Control

### Role → Department mapping

| Role | Allowed departments |
|---|---|
| `admin` | all four |
| `engineering` | `engineering` only |
| `hr` | `hr` only |
| `operations` | `operations` only |
| `support` | `product_support` only |

### How enforcement works (currently)

1. User logs in → JWT is issued with `role` and `departments_allowed` as claims
2. Every protected endpoint calls `get_current_user()` which decodes the JWT
3. The chat and documents endpoints call `allowed_departments()` which validates the requested department against the user's claim
4. The resolved department list is available for use as a Qdrant filter

### What's implemented vs what's pending

| Control | Status |
|---|---|
| JWT authentication on all endpoints | ✅ Done |
| Admin-only upload | ✅ Done |
| Department scope enforced on document listing | ✅ Done |
| Department scope resolved in chat router | ✅ Done (resolved, not yet filtered) |
| Qdrant query filtered by department at search time | ⚠️ MetadataFilterBuilder built, not wired into retriever |

The gap: `MetadataFilterBuilder.department_filter()` exists and produces the correct Qdrant `Filter` object, but `VectorRetriever.retrieve()` and `HybridRetriever.retrieve()` don't accept a `filter` argument yet. Adding `query_filter: Optional[Filter] = None` to their signatures and passing it to `qdrant.query_points()` is the one-line fix.

---

## Chunking Strategies Explained

### Fixed Chunking (`FixedChunker`)
- **Splitter:** `RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=64)`
- **Behaviour:** Tries to split at character boundaries in order: paragraphs (`\n\n`), newlines (`\n`), spaces. Falls back to hard character cut at 512.
- **Good for:** Short FAQs, release notes, well-structured plain text
- **Risk:** Can split a policy clause mid-sentence; the answer to a question may straddle two chunks

### Advanced Chunking (`AdvancedChunker`)
- **Splitter:** Same size (512/64) but with explicit `separators=["\n\n", "\n", ". ", " "]`
- **Behaviour:** Strongly prefers paragraph and sentence boundaries before falling back to spaces. Produces chunks that tend to be complete thoughts.
- **Good for:** Policy documents, multi-step guides, incident reports with paragraph structure
- **Difference from fixed:** The separator priority list is explicit and sentence-aware; fixed uses the splitter's internal defaults

Both strategies produce `{ chunk_id: UUID, chunk_text: str }` dicts. The strategy used is stored in the Qdrant payload and in SQLite so it can be traced back.

---

## Retrieval Pipeline Explained

### Current pipeline (what actually runs)

```
Query → embed (BAAI/bge-base-en-v1.5) → Qdrant cosine search → cross-encoder rerank → top-5
```

This is **vector search + reranking**, branded as "hybrid" in preparation for BM25 integration.

### Score interpretation

| Field | Source | Meaning |
|---|---|---|
| `score` | Qdrant cosine similarity | 0–1, semantic similarity |
| `rerank_score` | CrossEncoder logit | Relative relevance, not bounded 0–1 |
| `confidence: "high"` | `top_score >= 0.5` | The best vector match is reasonably similar |
| `confidence: "low"` | `top_score < 0.5` | Weak match, answer may be partial |
| `confidence: "not_found"` | `results == []` | Nothing retrieved at all |

### Hallucination prevention

Two layers:
1. **No results gate:** If Qdrant returns nothing, the LLM is never called
2. **System prompt instruction:** The LLM is explicitly told to say `"I cannot find reliable information in the knowledge base."` if the provided context doesn't answer the question

The `min_retrieval_score = 0.08` config value is defined but not yet enforced as a second gate (post-retrieval score threshold).

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- A [Qdrant Cloud](https://cloud.qdrant.io) account (free tier works — create a cluster and get the URL + API key)
- A [Groq](https://console.groq.com) API key (free tier available)

### 1. Clone and set up backend

```bash
git clone <repo-url>
cd enterprise-rag

python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

> The first startup downloads two models: `BAAI/bge-base-en-v1.5` (~440MB) and `cross-encoder/ms-marco-MiniLM-L-6-v2` (~86MB). Do this before your demo.

### 2. Set up frontend

```bash
cd frontend
npm install
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env with your values
```

### 4. Create Qdrant collection

On first startup the backend attempts to use the collection. Run this once to create it:

```python
# From the backend root with venv active:
python -c "from app.rag.ingestion.qdrant_client_manager import QdrantClientManager; QdrantClientManager().create_collection()"
```

---

## Environment Variables

```env
# Qdrant Cloud (required)
QDRANT_URL=https://your-cluster-id.qdrant.io
QDRANT_API_KEY=your-qdrant-api-key

# Groq (required)
GROQ_API_KEY=your-groq-api-key

# Backend (optional — defaults shown)
DATABASE_URL=sqlite:///./rag_backend.db
SECRET_KEY=change-me-for-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Frontend
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

---

## Running the App

**Terminal 1 — Backend:**
```bash
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```
- API: `http://localhost:8000`
- Auto-docs: `http://localhost:8000/docs`
- DB and demo users are created automatically on first startup

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```
- UI: `http://localhost:5173`

---

## Mock Mode (Frontend-only dev)

The frontend ships with a full mock API interceptor. It is **active by default** because `src/main.tsx` imports `./api/mockSetup` on line 3.

When mock mode is on:
- No backend needed
- All API calls are intercepted and return hardcoded data with simulated delays
- Console logs `[Mock API] Interceptor activated`

To switch to the real backend, comment out or remove this line in `src/main.tsx`:
```typescript
import "./api/mockSetup"; // ← remove this line
```

Mock-only credentials: `admin/admin123`, `alice_hr/hr123`, `bob_eng/eng123`

---

## Demo Accounts

Seeded automatically by `auth_service.seed_demo_users()` on every startup (idempotent):

| Username | Password | Role | Department access |
|---|---|---|---|
| `admin` | `admin123` | admin | All departments |
| `alice_hr` | `hr123` | hr | HR only |
| `bob_eng` | `eng123` | engineering | Engineering only |
| `olivia_ops` | `ops123` | operations | Operations only |
| `sam_support` | `support123` | support | Product Support only |

---

## Known Issues and TODOs

| # | Issue | Location | Fix |
|---|---|---|---|
| 1 | **Metadata filter not wired into retriever** | `chat.py`, `vector_retriever.py`, `hybrid_retriever.py` | Add `query_filter` param to `retrieve()`, pass `MetadataFilterBuilder.department_filter()` result |
| 2 | **Mock mode active in production build** | `src/main.tsx` line 3 | Remove `import "./api/mockSetup"` before building for production |
| 3 | **`min_retrieval_score` not enforced** | `chat.py` | Add score threshold check after retrieval; return `not_found` if `top_score < settings.min_retrieval_score` |
| 4 | **`chunk_size`/`chunk_overlap` in config not used** | `config.py` vs `fixed_chunker.py` | Wire `settings.chunk_size` and `settings.chunk_overlap` into chunker constructors |
| 5 | **`ChunkingStrategy.semantic` ≠ `"advanced"` in pipeline** | `schemas.py` vs `ingest_pipeline.py` | Rename `AdvancedChunker` to `SemanticChunker` or update the enum value to `"advanced"` |
| 6 | **Chunks stored in SQLite but never queried** | `db_models.py` `Chunk` table | Either remove the table or use it as a fallback/audit store |
| 7 | **`search_chunks()` shim still in document_service** | `document_service.py` | Remove the deprecated function |
| 8 | **BM25 not implemented** | `hybrid_retriever.py` | Integrate `fastembed` sparse vectors and Qdrant's native hybrid search query |
| 9 | **No streaming responses** | `chat.py`, `groq_client.py` | Add Server-Sent Events support; Groq SDK supports streaming |
| 10 | **Token stored in localStorage** | `src/main.tsx` | Consider `httpOnly` cookie or memory-only storage for production |

