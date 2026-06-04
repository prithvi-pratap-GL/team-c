# Person 4: RAG Retrieval & Generation Layer

## Quick Start

### Prerequisites

```bash
pip install qdrant-client sentence-transformers groq
```

### Basic Usage

```python
from rag.retrieval import HybridRetriever
from rag.generation import PromptBuilder, GroqClientService

# Initialize components
retriever = HybridRetriever()
prompt_builder = PromptBuilder()
groq = GroqClientService()  # Requires GROQ_API_KEY env var

# Step 1: Retrieve relevant documents
query = "What is the policy on remote work?"
results = retriever.retrieve(query, top_k=10, rerank=True, rerank_top_k=5)

# Step 2: Build hallucination-safe prompts
system_prompt, user_prompt = prompt_builder.build_prompt(query, results)

# Step 3: Generate response
response = groq.generate(system_prompt, user_prompt, temperature=0.2)
print(response)
```

---

## Module Overview

### Retrieval Layer (`rag/retrieval/`)

#### 1. VectorRetriever
Dense vector similarity search using Qdrant and BAAI/bge-base-en-v1.5.

```python
from rag.retrieval import VectorRetriever

retriever = VectorRetriever()
results = retriever.retrieve("What policies apply to contractors?", top_k=5)

# Result schema:
# {
#     "score": 0.92,                          # Similarity score
#     "chunk_text": "...",                    # Retrieved text
#     "metadata": {
#         "chunk_id": "chunk_123",
#         "doc_id": "doc_456",
#         "doc_name": "Contractor_Handbook.pdf",
#         "department": "HR",
#         "category": "Policies",
#         "version": "1.0",
#         "doc_date": "2025-01-01",
#         "document_type": "handbook",
#         "chunking_strategy": "sentence"
#     }
# }
```

#### 2. MetadataFilterBuilder
Composable Qdrant filters for RBAC and governance.

```python
from rag.retrieval import MetadataFilterBuilder

# Single field filters
dept_filter = MetadataFilterBuilder.department_filter(["HR", "Engineering"])
cat_filter = MetadataFilterBuilder.category_filter(["Benefits"])

# Combined AND filters
combined = MetadataFilterBuilder.combined_filter(
    departments=["HR", "Finance"],
    categories=["Policies", "Benefits"]
)
```

#### 3. Reranker
Cross-encoder reranking using ms-marco-MiniLM-L-6-v2.

```python
from rag.retrieval import get_reranker

reranker = get_reranker()  # Singleton
reranked = reranker.rerank(
    query="benefits of health insurance",
    results=vector_results,
    top_k=3
)
```

#### 4. HybridRetriever
Orchestrates vector retrieval and reranking.

```python
from rag.retrieval import HybridRetriever

hybrid = HybridRetriever()

# Without reranking
results = hybrid.retrieve(query, top_k=5, rerank=False)

# With reranking
results = hybrid.retrieve(query, top_k=10, rerank=True, rerank_top_k=5)
```

### Generation Layer (`rag/generation/`)

#### 1. PromptBuilder
Constructs hallucination-safe prompts for LLM generation.

```python
from rag.generation import PromptBuilder

pb = PromptBuilder()

# Build formatted context from retrieval results
context = pb.build_context(retrieval_results)

# Build complete prompts
system_prompt, user_prompt = pb.build_prompt(query, retrieval_results)
```

**System Prompt Guarantees:**
- Answers ONLY from supplied context
- Falls back to: "I cannot find reliable information in the knowledge base."
- Enforces source citation from document metadata
- Prevents hallucination through explicit instructions

#### 2. GroqClientService
Groq LLM generation wrapper.

```python
from rag.generation import GroqClientService

groq = GroqClientService(
    model="llama-3.3-70b-versatile",  # default
    api_key=None  # reads from GROQ_API_KEY env var
)

response = groq.generate(
    system_prompt="You are an assistant...",
    user_prompt="What is the policy?",
    temperature=0.2,
    max_tokens=1024
)
```

---

## Complete Pipeline Example

```python
from rag.retrieval import HybridRetriever
from rag.generation import PromptBuilder, GroqClientService
import logging

logging.basicConfig(level=logging.INFO)

def rag_pipeline(user_query: str) -> str:
    """Complete RAG pipeline from query to answer."""
    
    # Initialize (reuse instances in production)
    retriever = HybridRetriever()
    prompt_builder = PromptBuilder()
    groq = GroqClientService()
    
    # Step 1: Dense vector retrieval (top 10)
    retrieval_results = retriever.retrieve(
        query=user_query,
        top_k=10,
        rerank=False
    )
    
    # Step 2: Cross-encoder reranking (top 5)
    reranked_results = retriever.reranker.rerank(
        query=user_query,
        results=retrieval_results,
        top_k=5
    )
    
    # Step 3: Build hallucination-safe prompts
    system_prompt, user_prompt = prompt_builder.build_prompt(
        query=user_query,
        retrieval_results=reranked_results
    )
    
    # Step 4: Generate final response
    final_answer = groq.generate(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.2,
        max_tokens=1024
    )
    
    return final_answer

if __name__ == "__main__":
    query = "What is the company policy on flexible work arrangements?"
    answer = rag_pipeline(query)
    print(f"Q: {query}")
    print(f"A: {answer}")
```

---

## Architecture

```
User Query
    ↓
┌─────────────────────────────────────────────┐
│         RETRIEVAL LAYER                     │
│  ┌────────────────────────────────────────┐ │
│  │ HybridRetriever                        │ │
│  │  ├─ VectorRetriever                   │ │
│  │  │  ├─ Embedder (BAAI/bge-base)      │ │
│  │  │  └─ QdrantClientManager           │ │
│  │  └─ Reranker (singleton)             │ │
│  │     └─ cross-encoder/ms-marco        │ │
│  └────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│         GENERATION LAYER                    │
│  ┌────────────────────────────────────────┐ │
│  │ PromptBuilder                          │ │
│  │  └─ build_prompt()                    │ │
│  │     └─ Hallucination guards           │ │
│  └────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────┐ │
│  │ GroqClientService                      │ │
│  │  └─ generate()                        │ │
│  │     └─ llama-3.3-70b-versatile        │ │
│  └────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
    ↓
Final Answer
```

---

## Configuration

### Environment Variables

```bash
# Required for text generation
export GROQ_API_KEY="your-groq-api-key"

# Optional (defaults provided)
export QDRANT_URL="http://localhost:6333"
```

### Module Configuration

```python
# Custom Qdrant URL
retriever = HybridRetriever(qdrant_url="http://qdrant.example.com:6333")

# Custom Groq model
groq = GroqClientService(model="llama-3.1-405b-reasoning")

# Custom temperature (0.0-2.0)
response = groq.generate(system, user, temperature=0.5)
```

---

## Error Handling

All modules validate inputs and raise meaningful exceptions:

```python
from rag.retrieval import VectorRetriever

retriever = VectorRetriever()

try:
    # Empty query → ValueError
    retriever.retrieve("")
except ValueError as e:
    print(f"Invalid input: {e}")

try:
    # Qdrant connection failure → Exception with context
    results = retriever.retrieve("what is the policy?")
except Exception as e:
    print(f"Retrieval failed: {e}")
```

---

## Production Considerations

### Singleton Pattern
The Reranker uses singleton pattern to reuse model across requests:
```python
from rag.retrieval import get_reranker

reranker1 = get_reranker()
reranker2 = get_reranker()
assert reranker1 is reranker2  # True
```

### Caching Strategy
```python
# Option 1: Reuse instances
retriever = HybridRetriever()
groq = GroqClientService()

for query in queries:
    results = retriever.retrieve(query)
    # reuses embedder and reranker
```

### Logging
Enable debug logging to track pipeline execution:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
# Detailed logs from each module
```

### Performance Tips
1. **Batch embeddings** if possible
2. **Reuse retriever instances** (especially embedder)
3. **Cache frequently accessed documents**
4. **Adjust top_k parameters** based on latency requirements
5. **Use lower temperature** for deterministic output

---

## Testing

Run integration tests:
```bash
cd backend/app/rag
python integration_test.py
```

Expected output shows module validation and error handling tests.

---

## File Structure

```
rag/
├── __init__.py
├── retrieval/
│   ├── __init__.py                 # Clean exports
│   ├── vector_retriever.py         # Dense retrieval
│   ├── metadata_filter.py          # Filter builders
│   ├── rerankers.py                # Cross-encoder reranking
│   └── hybrid_retriever.py         # Orchestration
├── generation/
│   ├── __init__.py                 # Clean exports
│   ├── groq_client.py              # LLM wrapper
│   └── prompt_builder.py           # Prompt construction
├── example_usage.py                # Usage examples
└── integration_test.py             # Test suite
```

---

## Contracts & Frozen Interfaces

### Qdrant Collection
- **Name:** `enterprise_docs`
- **Distance:** COSINE
- **Dimension:** 768
- **Manager:** Reused from `rag.ingestion.qdrant_client_manager`

### Embeddings
- **Model:** BAAI/bge-base-en-v1.5
- **Dimension:** 768
- **Reused:** From `rag.ingestion.embedder`

### Payload Schema (Frozen)
```python
{
    "chunk_id": str,
    "doc_id": str,
    "doc_name": str,
    "department": str,
    "category": str,
    "version": str,
    "doc_date": str,
    "document_type": str,
    "chunk_text": str,
    "chunking_strategy": str
}
```

---

## Notes for Integration

### With FastAPI
```python
from fastapi import FastAPI, HTTPException
from rag.retrieval import HybridRetriever
from rag.generation import PromptBuilder, GroqClientService

app = FastAPI()
retriever = HybridRetriever()
prompt_builder = PromptBuilder()
groq = GroqClientService()

@app.post("/ask")
async def ask_question(query: str):
    try:
        results = retriever.retrieve(query, top_k=10, rerank=True)
        system, user = prompt_builder.build_prompt(query, results)
        response = groq.generate(system, user)
        return {"answer": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### With React Frontend
The response from the RAG pipeline is clean, hallucination-guarded text suitable for direct display.

---

## Debugging

Enable detailed logging:
```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```

Check logs for:
- Embedding generation timing
- Qdrant search results
- Reranking scores
- Prompt construction
- Groq API calls

---

## Future Extensions

Designed for extensibility:

1. **BM25 Integration:** HybridRetriever architecture supports adding BM25 fusion
2. **Multi-stage Reranking:** Add additional reranker models in pipeline
3. **Caching:** Add embedding/result caching layer
4. **Filtering:** Integrate MetadataFilterBuilder into retrieval
5. **Monitoring:** Add metrics tracking for production observability

---

## Support & Documentation

- See `IMPLEMENTATION_SUMMARY.md` for detailed module documentation
- Run `example_usage.py` for working examples
- Run `integration_test.py` for validation
- Check inline docstrings for API details

---

**Implementation Status:** ✅ COMPLETE  
**Last Updated:** 2026-06-03  
**Person 4 Responsibility:** ✅ FULLY IMPLEMENTED
