"""Cross-encoder reranking for retrieval results."""

import logging
from typing import Optional

from app.config import get_settings

logger = logging.getLogger(__name__)


class Reranker:
    """Cross-encoder reranker using sentence-transformers.

    Uses model from settings (default: cross-encoder/ms-marco-MiniLM-L-6-v2).
    Implemented as singleton to reuse model across requests.
    """

    _instance: Optional["Reranker"] = None

    def __new__(cls) -> "Reranker":
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_name: Optional[str] = None):
        """Initialize reranker with cross-encoder model.

        Args:
            model_name: Cross-encoder model identifier. If None, reads from settings.
        """
        if self._initialized:
            return

        from sentence_transformers import CrossEncoder

        if model_name is None:
            model_name = get_settings().reranker_model

        self.model_name = model_name
        self.model = CrossEncoder(model_name)
        self._initialized = True
        logger.info(f"Loaded cross-encoder reranker: {model_name}")

    def rerank(
        self,
        query: str,
        results: list[dict],
        top_k: int = 5,
    ) -> list[dict]:
        """Rerank retrieval results using cross-encoder.

        Args:
            query: User query string.
            results: List of vector retrieval results with structure:
                {
                    "score": float,
                    "chunk_text": str,
                    "metadata": {...}
                }
            top_k: Number of top results to return.

        Returns:
            Reranked results in same schema, sorted by reranker score.

        Raises:
            ValueError: If inputs are invalid.
        """
        if not query or not isinstance(query, str) or query.strip() == "":
            logger.error(f"Invalid query: {query}")
            raise ValueError("Query must be a non-empty string")

        if not results or not isinstance(results, list):
            logger.error(f"Invalid results: {results}")
            raise ValueError("Results must be a non-empty list")

        if not all(isinstance(r, dict) for r in results):
            logger.error("All results must be dictionaries")
            raise ValueError("All results must be dictionaries")

        try:
            logger.debug(f"Reranking {len(results)} results for query")

            pairs = []
            for result in results:
                chunk_text = result.get("chunk_text", "")
                if chunk_text:
                    pairs.append([query, chunk_text])

            if not pairs:
                logger.warning("No valid chunk texts to rerank")
                return results[:top_k]

            scores = self.model.predict(pairs)

            logger.debug("=" * 80)
            logger.debug("RERANKER SCORES (BEFORE SORTING)")
            logger.debug("=" * 80)

            ranked_results = []
            for idx, score in enumerate(scores):
                result = results[idx].copy()
                result["rerank_score"] = float(score)
                ranked_results.append(result)

                # Log reranker score with context
                metadata = result.get("metadata", {})
                chunk_text = result.get("chunk_text", "")
                chunk_preview = chunk_text[:100] if chunk_text else "N/A"

                logger.debug(f"\nChunk {idx + 1}:")
                logger.debug(f"  Qdrant Score: {result.get('score', 0):.4f}")
                logger.debug(f"  Reranker Score: {score:.4f}")
                logger.debug(f"  Chunk ID: {metadata.get('chunk_id')}")
                logger.debug(f"  Department: {metadata.get('department')}")
                logger.debug(f"  Preview: {chunk_preview}...")

            ranked_results.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)

            logger.debug("=" * 80)
            logger.debug("RERANKER SCORES (AFTER SORTING)")
            logger.debug("=" * 80)

            final_results = ranked_results[:top_k]
            for idx, result in enumerate(final_results, 1):
                metadata = result.get("metadata", {})
                logger.debug(f"\nFinal Chunk {idx}:")
                logger.debug(f"  Reranker Score: {result.get('rerank_score', 0):.4f}")
                logger.debug(f"  Chunk ID: {metadata.get('chunk_id')}")
                logger.debug(f"  Department: {metadata.get('department')}")

            logger.debug("=" * 80)
            logger.info(f"Reranked and returned top {len(final_results)} results")

            return final_results

        except ValueError as e:
            logger.error(f"Validation error in rerank: {e}")
            raise
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            raise


def get_reranker() -> Reranker:
    """Get or create singleton reranker instance.

    Returns:
        Singleton Reranker instance.
    """
    return Reranker()
