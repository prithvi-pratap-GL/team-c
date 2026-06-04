from rag.retrieval.hybrid_retriever import HybridRetriever

retriever = HybridRetriever()

query = "How many paid leave days do employees receive?"

results = retriever.retrieve(
    query=query,
    top_k=5,
)

print("\nRESULT COUNT:", len(results))

for i, r in enumerate(results, 1):
    print(f"\nResult {i}")
    print("Score:", r.get("score"))
    print("Text:", r.get("chunk_text"))
    print("Metadata:", r.get("metadata"))