# Infrastructure & Deployment - Enterprise RAG Assistant

## Overview

This document covers the production infrastructure setup, containerization, CI/CD pipelines, and deployment procedures for the Enterprise RAG system.

## 1. Docker & Container Architecture

### Services

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose (docker-compose.yml)      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Frontend │  │ Backend  │  │ PostgreSQL  │ │ Qdrant  │   │
│  │ (React)  │  │ (FastAPI)│  │             │ │(Vectors)│   │
│  │ Port     │  │ Port     │  │ Port 5432   │ │ Port    │   │
│  │ 3000     │  │ 8000     │  │             │ │ 6333    │   │
│  └─────┬────┘  └────┬─────┘  └─────┬───────┘ └────┬────┘   │
│        │            │              │              │         │
│        └────────────────────────────────────────────┘         │
│                 rag-network (bridge)                         │
│                                                               │
│  ┌──────────┐  ┌──────────┐                                 │
│  │  Nginx   │  │  Redis   │                                 │
│  │ (Proxy)  │  │ (Cache)  │                                 │
│  │ Port 80  │  │ Port     │                                 │
│  │          │  │ 6379     │                                 │
│  └──────────┘  └──────────┘                                 │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Service Details

| Service | Image | Port | Purpose | Health Check |
|---------|-------|------|---------|--------------|
| **Frontend** | Node 18 | 3000 | React UI, chat interface | 10s interval |
| **Backend** | Python 3.11 | 8000 | FastAPI, RAG pipeline | /health endpoint |
| **PostgreSQL** | postgres:15-alpine | 5432 | Metadata, users, RBAC | pg_isready |
| **Qdrant** | qdrant/qdrant:latest | 6333 | Vector storage | HTTP /health |
| **Redis** | redis:7-alpine | 6379 | Query cache, embeddings | PING command |
| **Nginx** | nginx:alpine | 80 | Reverse proxy, routing | HTTP status |

### Network

- **Network Name**: `rag-network` (bridge driver)
- **Isolation**: All services communicate within private Docker network
- **External Access**: Nginx only exposes port 80 (HTTP)
- **Internal Communication**: Service name → DNS resolution (e.g., `backend:8000`)

## 2. Database Setup

### PostgreSQL Initialization

**File**: `infra/db/init.sql`

Automatically executed on first container start via Docker volume mount:
```yaml
volumes:
  - ./infra/db/init.sql:/docker-entrypoint-initdb.d/init.sql
```

### Database Schema

#### Users Table
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  username VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'engineering', 'hr', 'operations', 'support')),
  departments_allowed TEXT[] NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Purpose**: RBAC - enforce role-based and department-based access control

#### Documents Table
```sql
CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  doc_name VARCHAR(500) NOT NULL,
  department VARCHAR(100) NOT NULL,
  category VARCHAR(100) NOT NULL,
  version VARCHAR(50),
  doc_date DATE,
  chunk_count INTEGER DEFAULT 0,
  fixed_chunk_count INTEGER DEFAULT 0,
  semantic_chunk_count INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  created_by UUID REFERENCES users(id)
);
```

**Purpose**: Track all uploaded documents and metadata

#### Feedback Table
```sql
CREATE TABLE feedback (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_id VARCHAR(255) NOT NULL,
  user_id UUID REFERENCES users(id),
  query_text TEXT NOT NULL,
  response_text TEXT,
  helpful BOOLEAN,
  rating INTEGER CHECK (rating >= 1 AND rating <= 5),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Purpose**: Collect user feedback for continuous improvement

#### Chat Sessions Table
```sql
CREATE TABLE chat_sessions (
  id VARCHAR(255) PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  ended_at TIMESTAMP,
  messages_count INTEGER DEFAULT 0,
  feedback_provided BOOLEAN DEFAULT FALSE
);
```

**Purpose**: Track conversation sessions for context and analytics

#### Experiment Results Table
```sql
CREATE TABLE experiment_results (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  experiment_name VARCHAR(255) NOT NULL,
  experiment_type VARCHAR(50) NOT NULL,
  query_number INTEGER,
  query_text TEXT NOT NULL,
  retrieval_mode VARCHAR(50),
  chunking_strategy VARCHAR(50),
  score INTEGER CHECK (score >= 0 AND score <= 3),
  mrr FLOAT8,
  execution_time_ms INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Purpose**: Store evaluation metrics for optimization

### Demo Users

Auto-seeded on first start:

| Username | Password | Role | Departments |
|----------|----------|------|-------------|
| admin | admin123 | admin | all |
| alice_hr | hr123 | hr | hr |
| bob_eng | eng123 | engineering | engineering |
| charlie_ops | ops123 | operations | operations |
| diana_support | support123 | support | product_support |

## 3. Qdrant Vector Database Configuration

### Configuration File

**File**: `infra/qdrant/config.yaml`

```yaml
log_level: info

server:
  http:
    host: 0.0.0.0
    port: 6333
  grpc:
    host: 0.0.0.0
    port: 6334

storage:
  storage_path: ./storage
  snapshots_path: ./snapshots
  temp_path: ./temp
  wal:
    enabled: true
    wal_capacity_mb: 200

performance:
  max_search_batch_size: 100
  max_optimization_threads: 2
```

### Collections Setup

Two collections for experiment comparison:

#### `documents_fixed`
- **Chunking**: Fixed size (512 tokens, 64 overlap)
- **Embeddings**: OpenAI text-embedding-3-small (1536 dimensions)
- **Sparse**: BM25 for hybrid search
- **Use case**: Baseline retrieval

#### `documents_semantic`
- **Chunking**: Semantic (variable size, threshold=0.85)
- **Embeddings**: Same as fixed
- **Sparse**: Same as fixed
- **Use case**: Production quality answers

### Payload Structure

Every vector point stores:
```json
{
  "chunk_text": "The annual leave entitlement is 20 days per year...",
  "chunk_id": "550e8400-e29b-41d4-a716-446655440000",
  "doc_id": "550e8400-e29b-41d4-a716-446655440001",
  "doc_name": "HR Policy Handbook 2024",
  "department": "hr",
  "category": "policy",
  "version": "2.1",
  "doc_date": "2024-01-15",
  "page_number": 2,
  "chunking_strategy": "fixed",
  "char_offset": 5230
}
```

## 4. Nginx Reverse Proxy

### Configuration

**File**: `infra/nginx/nginx.conf`

**Purpose**: 
- Route external traffic to frontend (React app)
- Route `/api/` prefix to backend (FastAPI)
- Enforce HTTPS redirection
- Prevent access to sensitive files

### Routing Rules

```nginx
# Frontend (React)
location / {
    proxy_pass http://frontend:3000;
    # WebSocket upgrade for live reload
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
}

# API Gateway
location /api/ {
    proxy_pass http://backend:8000/;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

# Health check
location /health {
    proxy_pass http://backend:8000/health;
    access_log off;
}
```

### Request Flow

```
User (http://localhost)
    ↓
Nginx (port 80)
    ├─→ /          → Frontend (React, port 3000)
    ├─→ /api/v1/   → Backend (FastAPI, port 8000)
    └─→ /health    → Backend health check
```

## 5. Demo Data Seeding

### Script

**File**: `scripts/seed_documents.py`

Creates sample documents across all departments:

- **HR**: `hr_policy_handbook_2024.txt` — Leave, overtime policies
- **Engineering**: `engineering_deployment_guide.txt` — Rollback procedures
- **Operations**: `operations_incident_tracking.txt` — Incident INC-2024-003
- **Support**: `support_faq.txt` — Password reset, ticket retention

**Usage**:
```bash
python scripts/seed_documents.py
```

**Output**: Documents created in `sample_docs/` directory

Then ingest via API:
```bash
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "Authorization: Bearer <TOKEN>" \
  -F "file=@sample_docs/hr_policy_handbook_2024.txt" \
  -F "metadata={\"department\":\"hr\",\"category\":\"policy\"}"
```

## 6. Experiment Automation

### Script

**File**: `scripts/run_experiments.py`

Compares retrieval and chunking strategies:

**Experiments**:

1. **Retrieval Comparison** (Vector vs Hybrid)
   - Tests: 10 queries across 4 departments
   - Expected: Hybrid 70%, Vector 30%
   - Key insight: Hybrid excels at keyword-heavy queries (incident IDs)

2. **Chunking Comparison** (Fixed vs Semantic)
   - Tests: Leave policy table, rollback procedure
   - Expected: Semantic 100%, Fixed 50%
   - Key insight: Semantic preserves complete units

**Usage**:
```bash
cd scripts
python run_experiments.py
```

**Output**: `experiment_report_<timestamp>.md`

## 7. Testing Infrastructure

### Test Suites

#### `tests/test_api.py`
- Authentication endpoints (login)
- Chat endpoints (query, RBAC enforcement)
- Ingestion endpoints (PDF, TXT, status)
- Feedback endpoints
- Document listing endpoints

#### `tests/test_ingestion.py`
- Parser correctness (PDF, TXT)
- Chunking (fixed, semantic)
- Embedding generation
- Qdrant upsert success

#### `tests/test_retrieval.py`
- Vector search retrieval
- Hybrid search retrieval
- Reranking
- RBAC filtering
- Score threshold enforcement

### Running Tests

**Local**:
```bash
pytest tests/ --cov=backend --cov-report=html
```

**Docker**:
```bash
docker-compose run --rm backend pytest tests/
```

## 8. CI/CD Pipelines

### GitHub Actions Workflows

#### `.github/workflows/tests.yml`
**Triggers**: Push to main/develop/feat-*, PR to main/develop

**Jobs**:

1. **test** (Python 3.11)
   - Services: PostgreSQL, Qdrant, Redis
   - Runs: pytest with coverage
   - Reports: Codecov upload

2. **lint**
   - Tools: black, isort, flake8, mypy
   - Reports: Formatting violations

3. **docker-build**
   - Builds: backend, frontend, nginx images
   - Validates: Dockerfiles are functional

**Example output**:
```
Test Results:
  ✓ 24 passed in 3.45s
  ✓ Coverage: 87% (backend/)

Lint:
  ✓ black: OK
  ✓ isort: OK
  ✓ flake8: OK

Docker Build:
  ✓ backend:latest
  ✓ frontend:latest
  ✓ nginx:latest
```

#### `.github/workflows/deploy.yml`
**Triggers**: Push to main, manual trigger (workflow_dispatch)

**Jobs**:

1. **build-and-push** → GitHub Container Registry (ghcr.io)
   - Builds multi-layer Docker images
   - Tags: branch, git SHA, `latest`
   - Requires: GITHUB_TOKEN (automatic)

2. **security-scan**
   - Uses: Trivy vulnerability scanner
   - Scans: filesystem for known vulnerabilities
   - Reports: GitHub Security tab (SARIF format)

## 9. Local Development

### Quick Start

```bash
# 1. Clone and navigate
cd challenge/team-c

# 2. Create .env file
cp .env.example .env
# Edit .env with your OPENAI_API_KEY

# 3. Start all services
docker-compose up

# 4. Seed demo documents
docker-compose exec backend python scripts/seed_documents.py

# 5. Ingest documents
# (Use frontend at http://localhost or API directly)

# 6. Test
docker-compose run --rm backend pytest tests/

# 7. Access
# Frontend: http://localhost
# API: http://localhost/api/v1
# Backend docs: http://localhost:8000/docs
# Qdrant console: http://localhost:6333/dashboard
```

### Service Health Checks

```bash
# Check PostgreSQL
docker-compose exec postgres pg_isready -U rag_user

# Check Qdrant
curl http://localhost:6333/health

# Check Redis
docker-compose exec redis redis-cli ping

# Check Backend
curl http://localhost:8000/health

# Check Nginx
curl http://localhost/health
```

### Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f postgres
docker-compose logs -f qdrant
```

## 10. Production Deployment Checklist

- [ ] Update JWT_SECRET_KEY to secure value
- [ ] Set OPENAI_API_KEY in production .env
- [ ] Enable HTTPS in Nginx (SSL certificates)
- [ ] Configure PostgreSQL replication
- [ ] Set up Qdrant cluster mode
- [ ] Enable Redis Sentinel for failover
- [ ] Configure monitoring (Prometheus, Grafana)
- [ ] Set up log aggregation (ELK Stack)
- [ ] Enable backup strategy (PostgreSQL, Qdrant snapshots)
- [ ] Run security audit (OWASP, dependency scanning)
- [ ] Load testing (k6, locust)
- [ ] Disaster recovery plan

## Summary

**Infrastructure Highlights**:
✓ Containerized microservices (Docker Compose)
✓ Automated database initialization (PostgreSQL)
✓ Vector database (Qdrant) for hybrid search
✓ Reverse proxy (Nginx) for routing
✓ CI/CD pipelines (GitHub Actions)
✓ Comprehensive testing (pytest)
✓ Experiment automation (retrieval & chunking)
✓ Security scanning (Trivy)
✓ Production-ready architecture

**Person 5 (Infrastructure Lead) Responsibilities**:
✓ Docker & environment setup
✓ Database schema & seeding
✓ Qdrant configuration
✓ Nginx reverse proxy
✓ Demo data automation
✓ Experiment runner
✓ Testing infrastructure
✓ CI/CD pipelines
✓ Documentation & deployment guides
