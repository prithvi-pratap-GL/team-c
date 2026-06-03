# Quick Start - Enterprise RAG Git & Development

## Before You Start Coding

1. **Set up your environment**
   ```bash
   cd rag
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

2. **Start Docker services**
   ```bash
   docker-compose up -d
   docker-compose ps  # Verify all are "healthy"
   ```

3. **Verify backend starts**
   ```bash
   # In another terminal
   cd rag/backend
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   # Visit http://localhost:8000/docs to see API
   ```

## Your Work Today

You're responsible for three areas:

### 1. Backend API (`feat/p2-api-endpoints`, `feat/p2-auth-rbac`)
- [ ] Implement actual RAG pipeline in chat.py
- [ ] Add real database queries in ingest.py
- [ ] Wire up Qdrant retrieval
- [ ] Test endpoints with curl or Postman

**Files to edit**:
- `backend/app/routers/chat.py` — TODO: implement RAG pipeline
- `backend/app/routers/ingest.py` — TODO: parse documents
- `backend/app/routers/auth.py` — TODO: connect to database

### 2. Infrastructure (`feat/p5-infra-docker`)
- [ ] Verify docker-compose works
- [ ] Check all health checks pass
- [ ] Update seed data if needed

**Files to edit**:
- `docker-compose.yml` — Service configuration
- `infra/db/init.sql` — Database schema
- `infra/qdrant/config.yaml` — Qdrant settings

### 3. Evaluation (`feat/p5-evaluation-experiments`)
- [ ] Implement experiment_runner.py
- [ ] Run retrieval comparison (vector vs hybrid)
- [ ] Capture chunking comparison results

**Files to edit**:
- `evaluation/experiment_runner.py` — TODO: run experiments
- `evaluation/metrics.py` — Scoring and MRR calculation

## Git Cheat Sheet

### Start your day
```bash
cd rag
git checkout dev
git pull origin dev
git checkout feat/p2-api-endpoints  # YOUR BRANCH
git rebase origin/dev               # Stay in sync
```

### During development
```bash
git add backend/app/routers/chat.py
git commit -m "feat(backend): implement hybrid retrieval"
git push origin feat/p2-api-endpoints
```

### Keep branch updated
```bash
git fetch origin
git rebase origin/dev
git push origin feat/p2-api-endpoints --force-with-lease
```

### Before merge (at checkpoint)
```bash
git checkout dev
git pull origin dev
git merge --squash feat/p2-api-endpoints
git commit -m "feat(backend): implement chat endpoint"
git push origin dev
```

### See what you changed
```bash
git diff origin/dev...HEAD     # See all your changes
git log origin/dev..HEAD       # See your commits only
```

## Timeline Checkpoints

| Time | Milestone | Your Task |
|------|-----------|-----------|
| T+0 | Kickoff | Switch to your branch, start coding |
| T+30m | Foundations | Docker running, schemas frozen |
| T+60m | Ingestion | Person 3 has documents in Qdrant |
| T+90m | Checkpoint 1 | Merge components to dev |
| T+120m | Integration | End-to-end working |
| T+150m | Checkpoint 2 | Hybrid vs vector data captured |
| T+180m | Demo prep | Rehearsal |
| T+210m | Live demo | Show it to judges |

## Testing Your Work

### Test backend locally
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "bob_eng", "password": "eng123"}'
```

### Test database
```bash
# From another terminal
psql postgresql://rag_user:rag_password@localhost:5432/rag_db
# Then in psql:
SELECT * FROM users;
SELECT COUNT(*) FROM documents;
```

### Test Qdrant
```bash
curl http://localhost:6333/health
```

### Run evaluation
```bash
cd rag
python -m evaluation.experiment_runner
```

## Common Git Issues

**Q: I messed up a commit**
```bash
git reset --soft HEAD~1  # Undo, keep changes
git add .
git commit -m "corrected message"
```

**Q: I'm out of sync with dev**
```bash
git fetch origin
git rebase origin/dev
git push origin feat/p2-api-endpoints --force-with-lease
```

**Q: What did I change?**
```bash
git diff origin/dev  # See all changes
git log -10 --oneline  # See your commits
```

**Q: I accidentally committed to main**
```bash
git branch feat/save-my-work
git reset --hard origin/main
git checkout feat/save-my-work
```

## Key Files to Know

| File | Purpose | Owner |
|------|---------|-------|
| `docker-compose.yml` | Service orchestration | Person 5 |
| `backend/app/models/schemas.py` | API contracts (FROZEN T+30m) | Person 2 |
| `backend/app/routers/chat.py` | Query endpoint | Person 2 |
| `backend/app/routers/ingest.py` | Document upload | Person 2 |
| `infra/db/init.sql` | Database schema | Person 5 |
| `evaluation/metrics.py` | Scoring functions | Person 5 |

## Demo Users

Use these for testing:

| Username | Password | Access |
|----------|----------|--------|
| admin | admin123 | All departments |
| bob_eng | eng123 | Engineering only |
| alice_hr | hr123 | HR only |

## Questions?

1. See [GIT_WORKFLOW.md](GIT_WORKFLOW.md) for detailed git instructions
2. See [README.md](README.md) for architecture overview
3. Run `git help <command>` for any git question
4. Check [docker-compose.yml](docker-compose.yml) for service config

## Sprint Goal

Get a working RAG system in 4 hours that:
- ✅ Ingests documents (fixed & semantic chunks)
- ✅ Searches with vector and hybrid modes
- ✅ Enforces RBAC at retrieval layer
- ✅ Shows performance wins of hybrid search
- ✅ Demonstrates judges you understand RAG challenges

Good luck! 🚀
