"""Confidence scoring service for RAG answers."""

import logging
from typing import Dict, List, Optional

from app.config import get_settings
from app.models.schemas import Confidence

logger = logging.getLogger(__name__)


class ConfidenceService:
    """Calculate answer confidence based on retrieval scores."""

    def __init__(self):
        """Initialize with settings."""
        self.settings = get_settings()
        

    def calculate(
        self,
        results: List[Dict],
        has_reranker: bool = True,
    ) -> tuple[Confidence, Dict[str, any]]:
        """Calculate confidence and return debug info.

        Args:
            results: List of retrieval results with score and optional rerank_score.
            has_reranker: Whether results have been reranked.

        Returns:
            Tuple of (confidence_level, debug_info_dict)
        """
        if not results:
            return Confidence.not_found, {
                "reason": "no_results",
                "vector_score": None,
                "reranker_score": None,
            }
        
        print("\nTOP CHUNK")
        print(results[0]["chunk_text"])
        print()
        print("VECTOR:", results[0]["score"])
        print("RERANK:", results[0]["rerank_score"])

        top_result = results[0]
        vector_score = top_result.get("score", 0)
        reranker_score = top_result.get("rerank_score")

        # Priority: reranker score > vector score
        if has_reranker and reranker_score is not None:
            return self._calculate_from_reranker(reranker_score, vector_score)
        else:
            return self._calculate_from_vector(vector_score)

    def _calculate_from_reranker(
        self, reranker_score: float, vector_score: float
    ) -> tuple[Confidence, Dict[str, any]]:
        """Calculate confidence from reranker score (MS MARCO cross-encoder).

        Reranker score ranges typically: -5 to +5
        - > +3.0: Highly relevant (direct answer)
        - +1.0 to +3.0: Relevant (partial/contextual)
        - -1.0 to +1.0: Weakly relevant (keyword overlap)
        - < -1.0: Not relevant (anti-relevance signal)

        Args:
            reranker_score: Cross-encoder logit from MS MARCO reranker.
            vector_score: Qdrant cosine similarity (for reference).

        Returns:
            Tuple of (confidence, debug_dict)
        """
        if reranker_score >= self.settings.confidence_high_threshold:
            confidence = Confidence.high
            reason = "reranker_above_high_threshold"
        elif reranker_score >= self.settings.confidence_medium_threshold:
            confidence = Confidence.medium
            reason = "reranker_above_medium_threshold"
        elif reranker_score >= self.settings.confidence_low_threshold:
            confidence = Confidence.low
            reason = "reranker_above_low_threshold"
        else:
            confidence = Confidence.low
            reason = "reranker_below_low_threshold"

        debug_info = {
            "reason": reason,
            "vector_score": round(vector_score, 4) if vector_score else None,
            "reranker_score": round(reranker_score, 4),
            "score_type": "reranker",
            "high_threshold": self.settings.confidence_high_threshold,
            "medium_threshold": self.settings.confidence_medium_threshold,
            "low_threshold": self.settings.confidence_low_threshold,
        }
        return confidence, debug_info

    def _calculate_from_vector(self, vector_score: float) -> tuple[Confidence, Dict[str, any]]:
        """Calculate confidence from vector similarity score only.

        Used when reranking is disabled. Qdrant cosine similarity ranges [0, 1].
        - >= 0.70: High similarity (top 5-10% of embedding space)
        - 0.55-0.70: Moderate similarity (in neighborhood)
        - 0.40-0.55: Low similarity (sparse overlap)
        - < 0.40: No similarity

        Args:
            vector_score: Qdrant cosine similarity.

        Returns:
            Tuple of (confidence, debug_dict)
        """
        if vector_score >= self.settings.confidence_high_threshold_vector:
            confidence = Confidence.high
            reason = "vector_above_high_threshold"
        elif vector_score >= self.settings.confidence_medium_threshold_vector:
            confidence = Confidence.medium
            reason = "vector_above_medium_threshold"
        elif vector_score >= self.settings.min_retrieval_score:
            confidence = Confidence.low
            reason = "vector_above_min_threshold"
        else:
            confidence = Confidence.not_found
            reason = "vector_below_min_threshold"

        debug_info = {
            "reason": reason,
            "vector_score": round(vector_score, 4),
            "reranker_score": None,
            "score_type": "vector_only",
            "high_threshold": self.settings.confidence_high_threshold_vector,
            "medium_threshold": self.settings.confidence_medium_threshold_vector,
            "min_threshold": self.settings.min_retrieval_score,
        }
        return confidence, debug_info

    def explain(self, confidence: Confidence) -> str:
        """Get human-readable explanation of confidence level.

        Args:
            confidence: Confidence level.

        Returns:
            Explanation string.
        """
        explanations = {
            Confidence.high: (
                "High confidence - the system found direct answers with strong relevance signals"
            ),
            Confidence.medium: (
                "Medium confidence - the system found partially relevant information that addresses the query"
            ),
            Confidence.low: (
                "Low confidence - the system found weakly relevant information with limited confidence"
            ),
            Confidence.not_found: (
                "Answer not found - the system could not retrieve sufficient evidence from the knowledge base"
            ),
        }
        return explanations.get(confidence, "Unknown confidence level")

    def get_thresholds(self, use_reranker: bool = True) -> Dict[str, float]:
        """Get current confidence thresholds.

        Args:
            use_reranker: Whether to get reranker or vector thresholds.

        Returns:
            Dict with threshold values.
        """
        if use_reranker:
            return {
                "high": self.settings.confidence_high_threshold,
                "medium": self.settings.confidence_medium_threshold,
                "low": self.settings.confidence_low_threshold,
                "model": "ms-marco-cross-encoder",
            }
        else:
            return {
                "high": self.settings.confidence_high_threshold_vector,
                "medium": self.settings.confidence_medium_threshold_vector,
                "low": self.settings.min_retrieval_score,
                "model": "vector-similarity",
            }
