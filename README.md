# RAG Challenge

## Backend

The FastAPI backend is implemented under `backend/app`.

Run it locally:

```powershell
cd backend
py -3 -m pip install -r requirements.txt
py -3 -m uvicorn app.main:app --reload
```

Open the API docs at:

```text
http://127.0.0.1:8000/docs
```

Demo users:

```text
admin / admin123
alice_hr / hr123
bob_eng / eng123
olivia_ops / ops123
sam_support / support123
```

Implemented endpoints:

```text
POST /api/v1/auth/login
POST /api/v1/ingest
GET  /api/v1/documents
POST /api/v1/chat
POST /api/v1/feedback
GET  /
GET  /health
GET  /qdrant-health
```

RAG integration environment:

```text
QDRANT_URL=your-qdrant-cloud-url
QDRANT_API_KEY=your-qdrant-api-key
GROQ_API_KEY=your-groq-api-key
```

Backend orchestration:

```text
/ingest -> rag.ingestion.ingest_pipeline.IngestPipeline
/chat   -> rag.retrieval.HybridRetriever -> PromptBuilder -> GroqClientService
```

## Frontend

The React frontend is implemented under `frontend/src`.

Run it locally:

```powershell
cd frontend
npm install
npm run dev
```

Open the app at:

```text
http://127.0.0.1:5173
```

Keep the backend running at:

```text
http://127.0.0.1:8000
```
