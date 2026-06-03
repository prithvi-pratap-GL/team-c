# RAG Ingestion Pipeline Implementation

## Overview

Complete implementation of the Enterprise Knowledge Assistant ingestion pipeline. This module handles document parsing, metadata processing, chunking, embedding, and vector database indexing.

## Architecture

```
rag/
├── ingestion/
│   ├── parsers/
│   │   ├── pdf_parser.py      (TASK 2)
│   │   └── txt_parser.py      (TASK 2)
│   ├── chunkers/
│   │   ├── fixed_chunker.py   (TASK 4)
│   │   └── advanced_chunker.py (TASK 4)
│   ├── embedder.py            (TASK 5)
│   ├── metadata_processor.py   (TASK 3)
│   ├── qdrant_client_manager.py (TASK 1)
│   ├── ingest_pipeline.py     (TASK 6-8)
│   └── __init__.py
└── __init__.py

scripts/
└── seed_documents.py          (TASK 9)

tests/
└── test_ingestion.py          (TASK 10)
```

## Implementation Summary

### TASK 1: Qdrant Client Manager
- **File**: `rag/ingestion/qdrant_client_manager.py`
- **Responsibility**: Initialize and manage Qdrant client connection
- **Key Features**:
  - Singleton pattern for single client instance
  - Automatic collection creation if missing
  - Health check capability
  - Collection: `enterprise_docs` with 768-dim COSINE distance

### TASK 2: Document Parsers
- **Files**: `rag/ingestion/parsers/{pdf_parser.py, txt_parser.py}`
- **Responsibility**: Extract text from documents
- **PDF Parser**:
  - Uses `pypdf.PdfReader`
  - Extracts full text and page count
- **TXT Parser**:
  - UTF-8 encoding
  - Simple file reading

### TASK 3: Metadata Processor
- **File**: `rag/ingestion/metadata_processor.py`
- **Responsibility**: Validate and normalize metadata
- **Features**:
  - Required fields: department, category, version
  - Optional field: date
  - Normalization: lowercase, trim whitespace
  - Generates UUID for doc_id

### TASK 4: Chunkers
- **Files**: `rag/ingestion/chunkers/{fixed_chunker.py, advanced_chunker.py}`
- **Fixed Chunker**:
  - Size: 512 tokens
  - Overlap: 64 tokens
- **Advanced Chunker**:
  - Section-aware with custom separators: `["\n\n", "\n", ". ", " "]`
  - Same size and overlap as fixed
  - Preserves document structure

### TASK 5: Embedder
- **File**: `rag/ingestion/embedder.py`
- **Responsibility**: Convert text to vectors
- **Specifications**:
  - Model: `BAAI/bge-base-en-v1.5`
  - Dimension: 768
  - Batch processing support
  - Singleton pattern

### TASK 6-8: Ingest Pipeline & Qdrant Upsert
- **File**: `rag/ingestion/ingest_pipeline.py`
- **Main Flow**:
  1. File type detection
  2. Parser selection
  3. Metadata validation
  4. Chunking strategy selection
  5. Text embedding
  6. Qdrant vector + payload upsert
- **Dual Strategy Support**: Both fixed and advanced stored simultaneously
- **Payload Schema** (frozen):
  ```python
  {
    "chunk_id": str,           # UUID
    "doc_id": str,             # UUID
    "doc_name": str,           # filename
    "department": str,         # normalized
    "category": str,           # normalized
    "version": str,            # normalized
    "doc_date": str | null,    # ISO format
    "document_type": str,      # pdf or txt
    "chunk_text": str,         # actual content
    "chunking_strategy": str   # fixed or advanced
  }
  ```

### TASK 9: Seed Script
- **File**: `scripts/seed_documents.py`
- **Responsibility**: Load sample documents and ingest both strategies
- **Features**:
  - Creates 3 sample documents (company policy, technical docs, budget report)
  - Ingests each with both fixed and advanced chunking
  - Logs detailed progress
  - Verifies final collection state

### TASK 10: Tests
- **File**: `tests/test_ingestion.py`
- **Coverage**:
  - PDF parsing
  - TXT parsing
  - Metadata validation
  - Chunk generation
  - Embedding (integration tests marked with `@pytest.mark.integration`)
  - Qdrant insertion

## Requirements

### System Dependencies
- Python 3.9+
- Docker & Docker Compose (for Qdrant)

### Python Packages
```
qdrant-client==1.7.0
langchain==0.1.0
langchain-text-splitters==0.0.1
sentence-transformers==2.2.2
torch==2.0.1
pypdf==3.17.1
pytest==7.4.3
numpy==1.24.3
```

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start Qdrant Server
```bash
docker-compose up -d qdrant
```

Verify Qdrant is running:
```bash
curl http://localhost:6333/health
```

Expected response:
```json
{"status":"ok"}
```

### 3. Seed Sample Documents
```bash
python scripts/seed_documents.py
```

Expected output:
```
✓ Fixed: company_policy.txt - N chunks, doc_id=<uuid>
✓ Advanced: company_policy.txt - M chunks, doc_id=<uuid>
✓ Fixed: technical_docs.txt - ...
✓ Advanced: technical_docs.txt - ...
[etc]
Collection 'enterprise_docs' contains X points
```

## Usage

### Ingest a Single Document

```python
from rag.ingestion import IngestPipeline

pipeline = IngestPipeline()

result = pipeline.ingest_document(
    file_path="/path/to/document.txt",
    metadata={
        "department": "engineering",
        "category": "technical",
        "version": "1.0",
        "date": "2024-01-15",
    },
    chunking_strategy="fixed"  # or "advanced"
)

print(result)
# {
#     "status": "success",
#     "doc_id": "550e8400-e29b-41d4-a716-446655440000",
#     "chunks_created": 12,
#     "chunking_strategy": "fixed"
# }
```

### Run Tests

```bash
# All tests
pytest tests/test_ingestion.py -v

# Only unit tests (skip integration tests)
pytest tests/test_ingestion.py -v -m "not integration"

# Only integration tests
pytest tests/test_ingestion.py -v -m integration
```

## Design Decisions

### Why Singleton Pattern for Embedder and Qdrant Manager?
- Model loading is expensive (sentence-transformers takes ~10s)
- Client connection should be reused
- Ensures single source of truth for configuration

### Why Dual Chunking Strategies?
- Person 4 needs to compare retrieval quality
- Fixed: Consistent, predictable chunk sizes
- Advanced: Respects document structure, better context preservation

### Why Store Both Strategies in Same Collection?
- `chunking_strategy` field in payload allows filtering/comparison
- Points maintain semantic relationship (same vectors as source)
- Enables A/B testing of retrieval quality

### Why RecursiveCharacterTextSplitter?
- Stable, deterministic chunking
- Supports custom separators for structure awareness
- No semantic/ML-based splitting (enables reproducible evaluation)

### Why BAAI/bge-base-en-v1.5?
- Free, no API keys needed
- High quality embeddings for enterprise documents
- 768 dimensions is efficient
- Optimized for semantic search
- Local inference (privacy)

## Error Handling

All modules implement meaningful exception handling:

- **FileNotFoundError**: Missing documents
- **ValueError**: Invalid metadata, unsupported file types, malformed dates
- **UnicodeDecodeError**: Non-UTF8 text files

Errors are logged with context and returned in result dictionaries.

## Logging

All modules use Python's `logging` module:

```bash
# View detailed logs
python scripts/seed_documents.py
```

Logs include:
- Document parsing progress
- Chunk creation counts
- Embedding batch processing
- Qdrant upsert details
- Errors with full context

## API for Person 4 (Retrieval Team)

Person 4 can immediately build retrieval on top using:

```python
from qdrant_client import QdrantClient

client = QdrantClient(url="http://localhost:6333")

# Query the collection
search_results = client.search(
    collection_name="enterprise_docs",
    query_vector=[...],  # 768-dim vector
    limit=10,
    with_payload=True,  # Get all metadata
)

# Results include:
# - chunk_text: Actual document content
# - doc_id: Document identifier
# - chunking_strategy: Which strategy was used
# - department, category, version, etc: Full metadata
```

## Payload Schema Reference

Every point in Qdrant contains this structure:

| Field | Type | Source | Usage |
|-------|------|--------|-------|
| `chunk_id` | UUID | Generated | Unique chunk identifier |
| `doc_id` | UUID | Generated | Links chunks to source document |
| `doc_name` | str | Parsed | Original filename |
| `department` | str | Metadata | Filter by department |
| `category` | str | Metadata | Filter by category |
| `version` | str | Metadata | Document version tracking |
| `doc_date` | ISO str | Metadata | Document date for filtering |
| `document_type` | str | Parsed | pdf or txt |
| `chunk_text` | str | Chunk | Actual content to return to user |
| `chunking_strategy` | str | Pipeline | fixed or advanced (for A/B testing) |

## Troubleshooting

### Qdrant Connection Failed
```bash
# Check if Qdrant is running
docker ps | grep qdrant

# View Qdrant logs
docker logs $(docker ps -q -f "label=com.docker.compose.service=qdrant")

# Restart Qdrant
docker-compose down && docker-compose up -d qdrant
```

### Model Download Fails
```bash
# Manually download BAAI/bge-base-en-v1.5
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-base-en-v1.5')"
```

### UTF-8 Decoding Error on Text Files
- Ensure text files are UTF-8 encoded
- Convert if needed: `iconv -f latin1 -t utf-8 file.txt > file_utf8.txt`

### Memory Usage for Large Documents
- Embedding is batched (default 32 at a time)
- For very large documents (>1M tokens), process in separate scripts

## Next Steps for Person 4

Once this pipeline is running, Person 4 can:

1. Query `enterprise_docs` collection in Qdrant
2. Use vector similarity to find relevant chunks
3. Apply reranking (their responsibility)
4. Assemble context for prompt
5. Call Groq for generation
6. Implement source attribution from chunk metadata

The payload structure provides all necessary context for RAG assembly.

## Files Inventory

✓ All 10 tasks implemented
✓ Modular, testable design
✓ Type hints throughout
✓ Comprehensive logging
✓ Docker-ready
✓ Full test coverage
✓ Production-ready error handling
