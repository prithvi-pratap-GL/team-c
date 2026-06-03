"""Cross-encoder reranking for retrieval results."""

import logging

logger = logging.getLogger(__name__)


class Reranker:
    """Cross-encoder reranker using sentence-transformers.

    Uses cross-encoder/ms-marco-MiniLM-L-6-v2 for ranking relevance.
    Implemented as singleton to reuse model across requests.
    """

    _instance: "Reranker | None" = None

    def __new__(cls) -> "Reranker":
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """Initialize reranker with cross-encoder model.

        Args:
            model_name: Cross-encoder model identifier.
        """
        if self._initialized:
            return

        from sentence_transformers import CrossEncoder

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

            ranked_results = []
            for idx, score in enumerate(scores):
                result = results[idx].copy()
                result["rerank_score"] = float(score)
                ranked_results.append(result)

            ranked_results.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)

            final_results = ranked_results[:top_k]
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
