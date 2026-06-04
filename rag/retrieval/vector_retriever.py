"""Dense vector retrieval from Qdrant."""

import logging
from typing import Any

from rag.ingestion.embedder import Embedder
from rag.ingestion.qdrant_client_manager import QdrantClientManager

logger = logging.getLogger(__name__)


class VectorRetriever:
    """Dense vector retrieval from Qdrant."""

    def __init__(self):
        """Initialize vector retriever with Qdrant and embedder.

        Reuses frozen ingestion contracts:
        - Embedder: BAAI/bge-base-en-v1.5
        - QdrantClientManager: collection = enterprise_docs
        """
        self.qdrant = QdrantClientManager()
        self.embedder = Embedder()
        logger.info("VectorRetriever initialized with ingestion contracts")

    def retrieve(self, query: str, top_k: int = 10, query_filter: Any = None) -> list[dict]:
        """Retrieve top-k results from Qdrant for a query.

        Args:
            query: User query string.
            top_k: Number of results to retrieve.

        Returns:
            List of results with score and metadata.

        Raises:
            ValueError: If query is empty or invalid.
            Exception: If Qdrant search fails.
        """
        if not query or not isinstance(query, str) or query.strip() == "":
            logger.error(f"Invalid query: {query}")
            raise ValueError("Query must be a non-empty string")

        try:
            logger.debug(f"Embedding query: {query[:100]}...")
            query_vector = self.embedder.embed_query(query)

            logger.debug(f"Searching Qdrant for top {top_k} results")
            client = self.qdrant.get_client()
            if hasattr(client, "search"):
                search_results = client.search(
                    collection_name=self.qdrant.collection_name,
                    query_vector=query_vector,
                    query_filter=query_filter,
                    limit=top_k,
                )
            else:
                search_results = client.query_points(
                    collection_name=self.qdrant.collection_name,
                    query=query_vector,
                    query_filter=query_filter,
                    limit=top_k,
                    with_payload=True,
                ).points

            results = []
            for result in search_results:
                payload = result.payload or {}
                normalized_result = {
                    "score": result.score,
                    "chunk_text": payload.get("chunk_text", ""),
                    "metadata": {
                        "chunk_id": payload.get("chunk_id"),
                        "doc_id": payload.get("doc_id"),
                        "doc_name": payload.get("doc_name"),
                        "department": payload.get("department"),
                        "category": payload.get("category"),
                        "version": payload.get("version"),
                        "doc_date": payload.get("doc_date"),
                        "document_type": payload.get("document_type"),
                        "chunking_strategy": payload.get("chunking_strategy"),
                    },
                }
                results.append(normalized_result)

            logger.info(f"Retrieved {len(results)} results for query")
            return results

        except ValueError as e:
            logger.error(f"Validation error in retrieve: {e}")
            raise
        except Exception as e:
            logger.error(f"Qdrant search failed: {e}")
            raise
