# Quick Start Guide

## 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Expected time**: 3-5 minutes (first-time model download)

## 2. Start Qdrant Docker Container

```bash
docker-compose up -d qdrant
```

**Verify**:
```bash
curl http://localhost:6333/health
```

Expected response: `{"status":"ok"}`

## 3. Seed Sample Documents

```bash
python scripts/seed_documents.py
```

**Expected output**:
```
Starting document seeding process
Ensuring Qdrant collection exists
Qdrant health check passed
Created 3 sample documents
Ingesting company_policy.txt with FIXED chunking strategy
✓ Fixed: company_policy.txt - 5 chunks, doc_id=...
✓ Advanced: company_policy.txt - 5 chunks, doc_id=...
[etc]
Collection 'enterprise_docs' contains 30 points
```

## 4. Verify Collection is Queryable

```bash
python -c "
from qdrant_client import QdrantClient
client = QdrantClient(url='http://localhost:6333')
collection = client.get_collection('enterprise_docs')
print(f'Collection has {collection.points_count} points')
"
```

## 5. Run Tests (Optional)

```bash
# Unit tests only
pytest tests/test_ingestion.py -v -m "not integration"

# All tests (including integration)
pytest tests/test_ingestion.py -v
```

## What's Been Implemented

### ✓ TASK 1: Qdrant Client Manager
- Singleton pattern client
- Automatic collection initialization
- Health checks

### ✓ TASK 2: Document Parsers
- PDF parsing with pypdf
- UTF-8 text parsing
- Consistent interface

### ✓ TASK 3: Metadata Processor
- Field validation (department, category, version)
- Normalization (lowercase, trim)
- UUID generation

### ✓ TASK 4: Chunkers
- Fixed: 512 size, 64 overlap
- Advanced: Section-aware with custom separators
- Both strategies stored simultaneously

### ✓ TASK 5: Embedder
- sentence-transformers with BAAI/bge-base-en-v1.5
- 768-dimensional vectors
- Batch processing
- Singleton pattern

### ✓ TASK 6-8: Ingest Pipeline & Qdrant Upsert
- Complete document-to-vector flow
- Dual chunking strategy support
- Full payload schema compliance
- Meaningful error handling

### ✓ TASK 9: Seed Script
- 3 sample documents
- Both chunking strategies
- Automatic ingestion

### ✓ TASK 10: Tests
- PDF/TXT parsing tests
- Metadata validation tests
- Chunker tests
- Embedding tests
- End-to-end pipeline tests

## Folder Structure

```
rag challenge/
├── rag/
│   ├── ingestion/
│   │   ├── parsers/
│   │   │   ├── pdf_parser.py
│   │   │   ├── txt_parser.py
│   │   │   └── __init__.py
│   │   ├── chunkers/
│   │   │   ├── fixed_chunker.py
│   │   │   ├── advanced_chunker.py
│   │   │   └── __init__.py
│   │   ├── embedder.py
│   │   ├── qdrant_client_manager.py
│   │   ├── metadata_processor.py
│   │   ├── ingest_pipeline.py
│   │   └── __init__.py
│   └── __init__.py
├── scripts/
│   ├── seed_documents.py
│   └── __init__.py
├── tests/
│   ├── test_ingestion.py
│   └── __init__.py
├── requirements.txt
├── docker-compose.yml
├── conftest.py
├── IMPLEMENTATION.md
└── SETUP.md
```

## API for Person 4 (Retrieval Team)

Collection name: `enterprise_docs`

Each point includes:
- `chunk_text`: The actual document content
- `doc_id`: Document identifier
- `chunking_strategy`: "fixed" or "advanced"
- All metadata: department, category, version, date, etc.

Example query:
```python
from qdrant_client import QdrantClient

client = QdrantClient(url="http://localhost:6333")
results = client.search(
    collection_name="enterprise_docs",
    query_vector=[...],  # 768-dim embedding
    limit=10,
    with_payload=True,
)

# Results have all metadata + chunk_text for context window
```

## Key Design Decisions

1. **Singleton Embedder/Qdrant**: Expensive to initialize, reused across requests
2. **Dual Chunking Strategies**: Different chunk boundaries for A/B testing retrieval
3. **Fixed Payload Schema**: Frozen to avoid breaking Person 4's code
4. **Local Embeddings**: No API calls, no latency, reproducible
5. **RecursiveCharacterTextSplitter**: Stable, structure-aware, deterministic

## Troubleshooting

**Qdrant won't start**:
```bash
docker-compose down
docker-compose up -d qdrant --force-recreate
```

**Model download fails**:
```bash
# Download manually
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-base-en-v1.5')"
```

**Connection refused**:
```bash
# Wait for Qdrant to fully start
sleep 10
python scripts/seed_documents.py
```

## Status: READY FOR PERSON 4

✓ All 10 tasks complete
✓ Pipeline fully functional
✓ Collection `enterprise_docs` populated
✓ Payload schema fixed
✓ Docker-ready
✓ Type hints throughout
✓ Comprehensive logging
✓ Full test coverage

Person 4 can immediately build retrieval on this foundation.
