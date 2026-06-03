"""Hybrid retrieval orchestration combining vector and BM25 search."""

import logging
from typing import Optional

from rag.retrieval.rerankers import get_reranker
from rag.retrieval.vector_retriever import VectorRetriever

# Optional is used in retrieve() method signature

logger = logging.getLogger(__name__)


class HybridRetriever:
    """Hybrid retrieval combining dense vector search with optional BM25.

    Orchestrates VectorRetriever and Reranker, with extensibility for
    future BM25 integration.
    """

    def __init__(self):
        """Initialize hybrid retriever.

        Uses frozen ingestion contracts:
        - VectorRetriever: reuses Embedder and QdrantClientManager
        - Reranker: singleton cross-encoder model
        """
        self.vector_retriever = VectorRetriever()
        self.reranker = get_reranker()
        logger.info("HybridRetriever initialized with vector retrieval")

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        rerank: bool = True,
        rerank_top_k: Optional[int] = None,
    ) -> list[dict]:
        """Retrieve documents using hybrid strategy.

        Current implementation: vector retrieval + optional reranking.
        Designed to accommodate future BM25 fusion.

        Args:
            query: User query string.
            top_k: Number of vector results to retrieve.
            rerank: Whether to apply cross-encoder reranking.
            rerank_top_k: Number of results to return after reranking.
                         If None, defaults to top_k.

        Returns:
            List of results with scores and metadata.

        Raises:
            ValueError: If query is invalid.
            Exception: If retrieval fails.
        """
        if not query or not isinstance(query, str) or query.strip() == "":
            logger.error(f"Invalid query: {query}")
            raise ValueError("Query must be a non-empty string")

        try:
            logger.debug(f"Hybrid retrieval: query='{query[:100]}...', top_k={top_k}, rerank={rerank}")

            vector_results = self.vector_retriever.retrieve(query, top_k=top_k)
            logger.info(f"Vector retrieval returned {len(vector_results)} results")

            if not rerank:
                logger.debug("Reranking disabled, returning vector results")
                return vector_results

            if rerank_top_k is None:
                rerank_top_k = min(top_k, len(vector_results))

            final_results = self.reranker.rerank(
                query=query,
                results=vector_results,
                top_k=rerank_top_k,
            )
            logger.info(f"Reranking returned {len(final_results)} results")

            return final_results

        except ValueError as e:
            logger.error(f"Validation error in hybrid retrieve: {e}")
            raise
        except Exception as e:
            logger.error(f"Hybrid retrieval failed: {e}")
            raise
