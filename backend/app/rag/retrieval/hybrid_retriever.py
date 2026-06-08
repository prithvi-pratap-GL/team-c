"""Hybrid retrieval orchestration combining vector and BM25 search."""

import logging
from typing import Optional

from qdrant_client.models import Filter

from app.rag.retrieval.rerankers import get_reranker
from app.rag.retrieval.vector_retriever import VectorRetriever

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
        query_filter: Optional[Filter] = None,
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
            query_filter: Optional Qdrant filter to scope results (e.g., by department).

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
            logger.debug(
                f"Hybrid retrieval: query='{query[:100]}...', top_k={top_k}, "
                f"rerank={rerank}" + (f", filter={query_filter}" if query_filter else "")
            )

            vector_results = self.vector_retriever.retrieve(
                query, top_k=top_k, query_filter=query_filter
            )
            logger.info(
                f"Vector retrieval returned {len(vector_results)} results"
                + (" (with filter)" if query_filter else "")
            )

            if not rerank:
                logger.debug("Reranking disabled, returning vector results as-is")
                logger.debug("=" * 80)
                logger.debug("FINAL RESULTS (NO RERANKING) - USING QDRANT SCORES")
                logger.debug("=" * 80)
                for idx, result in enumerate(vector_results, 1):
                    metadata = result.get("metadata", {})
                    chunk_text = result.get("chunk_text", "")
                    chunk_preview = chunk_text[:100] if chunk_text else "N/A"
                    logger.debug(f"\nFinal Chunk {idx}:")
                    logger.debug(f"  Score (Qdrant): {result.get('score', 0):.4f}")
                    logger.debug(f"  Chunk ID: {metadata.get('chunk_id')}")
                    logger.debug(f"  Department: {metadata.get('department')}")
                    logger.debug(f"  Preview: {chunk_preview}...")
                logger.debug("=" * 80)
                return vector_results

            if rerank_top_k is None:
                rerank_top_k = min(top_k, len(vector_results))

            final_results = self.reranker.rerank(
                query=query,
                results=vector_results,
                top_k=rerank_top_k,
            )

            logger.debug("=" * 80)
            logger.debug("FINAL RESULTS (AFTER RERANKING) - USING RERANKER SCORES")
            logger.debug("=" * 80)
            for idx, result in enumerate(final_results, 1):
                metadata = result.get("metadata", {})
                chunk_text = result.get("chunk_text", "")
                chunk_preview = chunk_text[:100] if chunk_text else "N/A"
                logger.debug(f"\nFinal Chunk {idx}:")
                logger.debug(f"  Score (Reranker): {result.get('rerank_score', 0):.4f}")
                logger.debug(f"  Score (Qdrant - original): {result.get('score', 0):.4f}")
                logger.debug(f"  Chunk ID: {metadata.get('chunk_id')}")
                logger.debug(f"  Department: {metadata.get('department')}")
                logger.debug(f"  Preview: {chunk_preview}...")
            logger.debug("=" * 80)

            logger.info(f"Reranking returned {len(final_results)} results")

            return final_results

        except ValueError as e:
            logger.error(f"Validation error in hybrid retrieve: {e}")
            raise
        except Exception as e:
            logger.error(f"Hybrid retrieval failed: {e}")
            raise
