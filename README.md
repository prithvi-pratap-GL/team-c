# Enterprise RAG Assistant

A production-grade Retrieval-Augmented Generation (RAG) system for enterprise document search with hybrid retrieval, role-based access control, and comprehensive evaluation metrics.

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)
- OpenAI API key

### Setup

1. **Clone and navigate to rag directory**
   ```bash
   cd rag
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

2. **Start all services** (Person 5 - Infra, T+0 to T+30m)
   ```bash
   docker-compose up -d
   # Wait for health checks to pass (~30s)
   ```

3. **Verify services are running**
   ```bash
   docker-compose ps
   # All should show "healthy" status
   ```

4. **Access the API**
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Postgres: localhost:5432
   - Qdrant: http://localhost:6333

## Project Structure

```
rag/
├── backend/              # FastAPI application (Person 2)
│   ├── app/
│   │   ├── main.py      # Main FastAPI app
│   │   ├── config.py    # Configuration management
│   │   ├── models/      # Pydantic schemas (FROZEN at T+30m)
│   │   └── routers/     # API endpoints (auth, chat, ingest, feedback)
│   ├── requirements.txt
│   └── Dockerfile
│
├── infra/               # Infrastructure (Person 5)
│   ├── db/
│   │   └── init.sql     # PostgreSQL initialization
│   └── qdrant/
│       └── config.yaml  # Qdrant configuration
│
├── evaluation/          # Evaluation & metrics (Person 5 + helpers)
│   ├── metrics.py       # Scoring functions & evaluation queries
│   └── experiment_runner.py  # Run experiments
│
├── rag/                 # RAG pipeline (Person 3 + 4)
│   ├── ingestion/       # Document parsing & chunking
│   └── retrieval/       # Vector & hybrid search
│
├── docker-compose.yml   # Services orchestration
└── README.md
```

## API Endpoints (T+30m Frozen Contracts)

### Authentication
```
POST /api/v1/auth/login
  Request: {username, password}
  Response: {access_token, role, departments_allowed}
```

### Chat / Query
```
POST /api/v1/chat
  Request: {query, filters, retrieval_mode, session_id}
  Response: {answer, sources, confidence, session_id}
```

### Ingestion
```
POST /api/v1/ingest
  Request: multipart form with file + metadata JSON
  Response: {job_id, status, doc_id}
```

### Feedback
```
POST /api/v1/feedback
  Request: {session_id, query, helpful, comment}
  Response: {status: "recorded"}
```

### Documents
```
GET /api/v1/documents?department=engineering&page=1
  Response: {documents, total, page}
```

## Demo Users

| Username | Password | Role | Departments |
|----------|----------|------|-------------|
| admin | admin123 | admin | All |
| alice_hr | hr123 | hr | HR only |
| bob_eng | eng123 | engineering | Engineering only |
| charlie_ops | ops123 | operations | Operations only |
| diana_support | support123 | support | Product Support only |

## Timeline (4-hour sprint)

- **T+0**: Kick off, branch creation, assignments
- **T+30m**: ✅ Docker Compose working, schemas.py frozen
- **T+60m**: ✅ First documents ingested into Qdrant
- **T+90m**: ✅ All components working in isolation, merge checkpoint 1
- **T+120m**: ✅ Full chat flow working end-to-end
- **T+150m**: ✅ Hybrid + vector comparison data captured
- **T+180m**: Demo rehearsal
- **T+210m**: Final demo

## Git Workflow

See [GIT_WORKFLOW.md](../GIT_WORKFLOW.md) for detailed instructions

### Key Rules
1. Always branch from `dev`, never from `main`
2. Squash-merge to dev
3. Commit format: `feat(scope): description`
4. Merge checkpoints at T+30m, T+90m, T+150m, T+210m

### Your Branches
- `feat/p2-api-endpoints` — Backend routes
- `feat/p2-auth-rbac` — Authentication & RBAC
- `feat/p5-infra-docker` — Docker infrastructure
- `feat/p5-seed-documents` — Demo data
- `feat/p5-evaluation-experiments` — Experiments & metrics

## Running Tests

```bash
# Unit tests
pytest tests/ -v

# Coverage report
pytest tests/ --cov=app

# Integration tests (requires services running)
pytest tests/integration/ -v
```

## Development

### Local Backend Setup (without Docker)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Database Migrations
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head
```

## Evaluation Experiments

### Retrieval Comparison (Vector vs Hybrid)
```bash
python -m evaluation.experiment_runner
```

### Chunking Comparison (Fixed vs Semantic)
Tests show hybrid excels at keyword queries (INC-2024-003, specific terms)
while vector-only struggles on exact matches.

## Architecture Notes

- **Metadata Store**: PostgreSQL (relational integrity, RBAC rules)
- **Vector DB**: Qdrant (hybrid search, metadata filtering, single container)
- **Cache**: Redis (embedding cache, query results, 5min TTL)
- **Framework**: LangChain (RAG pipeline composition)
- **Embedding**: text-embedding-3-small (1536-dim, fast, cheap)
- **LLM**: gpt-4o-mini (cost-effective, sufficient context)
- **Auth**: JWT with role-based access control at retrieval layer

## Troubleshooting

### Services won't start
```bash
# Check logs
docker-compose logs postgres
docker-compose logs qdrant
docker-compose logs backend

# Clean restart
docker-compose down -v
docker-compose up -d
```

### Database connection errors
- Verify PostgreSQL is healthy: `docker-compose ps`
- Check DATABASE_URL matches init.sql credentials
- Ensure postgres container has finished initialization (wait for health check)

### Qdrant connection errors
- Verify Qdrant is running on port 6333
- Check QDRANT_URL in .env
- Collections are created automatically on first ingest

## Next Steps (Post-Demo)

1. **Fine-tune embeddings** on enterprise vocabulary
2. **Implement streaming** for longer responses
3. **Add conversation context** for multi-turn support
4. **Monitor production performance** with dashboards
5. **Collect user feedback** to improve model
6. **Scale retrieval** with sharded Qdrant clusters

## Contributing

- Follow commit message format: `feat(scope): description`
- Test all changes before merging
- Update this README for architectural changes
- Document experiments in docs/experiment-results.md
