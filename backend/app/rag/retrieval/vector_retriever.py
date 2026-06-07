"""Dense vector retrieval from Qdrant."""

import logging
from typing import Optional

from qdrant_client.models import Filter

from app.rag.ingestion.embedder import Embedder
from app.rag.ingestion.qdrant_client_manager import QdrantClientManager

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

    def retrieve(
        self, query: str, top_k: int = 10, query_filter: Optional[Filter] = None
    ) -> list[dict]:
        """Retrieve top-k results from Qdrant for a query.

        Args:
            query: User query string.
            top_k: Number of results to retrieve.
            query_filter: Optional Qdrant filter to scope results (e.g., by department).

        Returns:
            List of results with score and metadata.
        """
        if not query or not isinstance(query, str) or query.strip() == "":
            logger.error(f"Invalid query: {query}")
            raise ValueError("Query must be a non-empty string")

        try:
            logger.debug(f"Embedding query: {query[:100]}...")

            query_vector = self.embedder.embed_query(query)

            client = self.qdrant.get_client()

            logger.debug(
                f"Searching Qdrant for top {top_k} results"
                + (f" with filter" if query_filter else "")
            )

            search_response = client.query_points(
                collection_name=self.qdrant.COLLECTION_NAME,
                query=query_vector,
                limit=top_k,
                query_filter=query_filter,
            )

            results = []

            for point in search_response.points:
                payload = point.payload or {}

                results.append(
                    {
                        "score": point.score,
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
                            "chunking_strategy": payload.get(
                                "chunking_strategy"
                            ),
                        },
                    }
                )

            logger.info(f"Retrieved {len(results)} results for query")
            return results

        except ValueError:
            raise

        except Exception as e:
            logger.error(f"Qdrant search failed: {e}")
            raise