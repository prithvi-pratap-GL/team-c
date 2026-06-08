"""Confidence Scoring Calibration and Testing.

This script tests the confidence system with realistic queries to validate thresholds.
It captures actual score distributions from both vector search and reranker.

Run with:
    python test_confidence_calibration.py
"""

import json
import logging
from typing import List, Dict, Any
import sys

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Add backend to path
sys.path.insert(0, "backend")

from app.rag.retrieval.hybrid_retriever import HybridRetriever
from app.rag.retrieval.metadata_filter import MetadataFilterBuilder
from app.services.confidence_service import ConfidenceService
from app.config import get_settings


# Test queries designed to capture different confidence levels
TEST_QUERIES = [
    # Expected HIGH confidence - direct questions about tech/policy
    {
        "query": "What is the tech stack we are using in our app?",
        "expected": "high",
        "description": "Direct tech question - should find specific answers",
    },
    {
        "query": "What is the company remote work policy?",
        "expected": "high",
        "description": "Policy question - should have documented answers",
    },

    # Expected MEDIUM confidence - broader topics
    {
        "query": "Tell me about the deployment process",
        "expected": "medium",
        "description": "Process-oriented - likely partial docs",
    },
    {
        "query": "What tools are available for development?",
        "expected": "medium",
        "description": "Tool discovery - scattered references",
    },

    # Expected LOW confidence - vague/cross-cutting queries
    {
        "query": "How do we handle security?",
        "expected": "low",
        "description": "Broad topic - many partial matches",
    },
    {
        "query": "What was the incident last week?",
        "expected": "low",
        "description": "Time-specific - may have partial matches",
    },

    # Expected NOT_FOUND - queries outside knowledge base
    {
        "query": "What is the capital of France?",
        "expected": "not_found",
        "description": "Out of domain - should have no matches",
    },
    {
        "query": "Tell me about quantum computing",
        "expected": "not_found",
        "description": "Out of domain - should have no matches",
    },
]


def test_single_query(retriever: HybridRetriever, confidence_svc: ConfidenceService, query_test: Dict[str, Any]) -> Dict[str, Any]:
    """Test a single query and return score breakdown.

    Args:
        retriever: HybridRetriever instance
        confidence_svc: ConfidenceService instance
        query_test: Test query dict with 'query', 'expected', 'description'

    Returns:
        Dict with test results including scores and confidence decision.
    """
    query = query_test["query"]
    expected = query_test["expected"]
    description = query_test["description"]

    logger.info(f"\n{'='*80}")
    logger.info(f"Testing: {query}")
    logger.info(f"Description: {description}")
    logger.info(f"Expected: {expected}")
    logger.info(f"{'='*80}")

    try:
        # Retrieve with reranking enabled
        results = retriever.retrieve(query=query, top_k=5, rerank=True, rerank_top_k=3)

        if not results:
            logger.warning("No results retrieved")
            return {
                "query": query,
                "expected": expected,
                "results_count": 0,
                "vector_scores": [],
                "reranker_scores": [],
                "predicted_confidence": "not_found",
                "confidence_correct": expected == "not_found",
                "details": "No results",
            }

        # Extract scores
        vector_scores = [r.get("score", 0) for r in results]
        reranker_scores = [r.get("rerank_score", 0) for r in results]

        logger.info(f"\nRetrieved {len(results)} results:")
        for idx, result in enumerate(results, 1):
            vec_score = result.get("score", 0)
            rer_score = result.get("rerank_score", 0)
            doc_name = result["metadata"].get("doc_name", "Unknown")
            logger.info(f"  Result {idx}: vec={vec_score:.4f} rer={rer_score:.4f} doc={doc_name}")

        # Calculate confidence
        has_reranker = len(reranker_scores) > 0 and reranker_scores[0] is not None
        confidence, debug_info = confidence_svc.calculate(results, has_reranker=has_reranker)

        logger.info(f"\nConfidence Calculation:")
        logger.info(f"  Score Type: {debug_info.get('score_type')}")
        logger.info(f"  Top Vector Score: {debug_info.get('vector_score')}")
        logger.info(f"  Top Reranker Score: {debug_info.get('reranker_score')}")
        logger.info(f"  Reason: {debug_info.get('reason')}")
        logger.info(f"  Predicted: {confidence.value}")
        logger.info(f"  Expected: {expected}")
        logger.info(f"  ✓ CORRECT" if confidence.value == expected else f"  ✗ MISMATCH")

        return {
            "query": query,
            "expected": expected,
            "predicted": confidence.value,
            "correct": confidence.value == expected,
            "results_count": len(results),
            "vector_scores": [round(s, 4) for s in vector_scores],
            "reranker_scores": [round(s, 4) for s in reranker_scores],
            "top_vector_score": round(vector_scores[0], 4) if vector_scores else None,
            "top_reranker_score": round(reranker_scores[0], 4) if reranker_scores else None,
            "confidence_reasoning": debug_info.get("reason"),
            "description": description,
        }

    except Exception as e:
        logger.error(f"Error testing query: {e}", exc_info=True)
        return {
            "query": query,
            "expected": expected,
            "error": str(e),
            "description": description,
        }


def main():
    """Run confidence calibration tests."""
    settings = get_settings()

    logger.info("\n" + "="*80)
    logger.info("CONFIDENCE SCORING CALIBRATION TEST")
    logger.info("="*80)
    logger.info(f"\nConfiguration:")
    logger.info(f"  Embedding Model: {settings.embedding_model}")
    logger.info(f"  Reranker Model: {settings.reranker_model}")
    logger.info(f"  LLM Model: {settings.llm_model}")
    logger.info(f"\nConfidence Thresholds (Reranker):")
    logger.info(f"  HIGH: >= {settings.confidence_high_threshold}")
    logger.info(f"  MEDIUM: >= {settings.confidence_medium_threshold}")
    logger.info(f"  LOW: >= {settings.confidence_low_threshold}")
    logger.info(f"\nConfidence Thresholds (Vector-only):")
    logger.info(f"  HIGH: >= {settings.confidence_high_threshold_vector}")
    logger.info(f"  MEDIUM: >= {settings.confidence_medium_threshold_vector}")
    logger.info(f"  LOW: >= {settings.min_retrieval_score}")

    try:
        retriever = HybridRetriever()
        confidence_svc = ConfidenceService()
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        logger.error("Make sure embeddings and reranker models are available")
        return

    results = []
    for test_query in TEST_QUERIES:
        result = test_single_query(retriever, confidence_svc, test_query)
        results.append(result)

    # Summary
    logger.info("\n" + "="*80)
    logger.info("TEST SUMMARY")
    logger.info("="*80)

    correct_count = sum(1 for r in results if r.get("correct", False))
    total_count = len(results)
    accuracy = (correct_count / total_count * 100) if total_count > 0 else 0

    logger.info(f"\nAccuracy: {correct_count}/{total_count} ({accuracy:.1f}%)")

    logger.info("\nResults by Expected Confidence Level:")
    for expected_level in ["high", "medium", "low", "not_found"]:
        level_results = [r for r in results if r.get("expected") == expected_level]
        if level_results:
            correct = sum(1 for r in level_results if r.get("correct", False))
            total = len(level_results)
            logger.info(f"\n{expected_level.upper()}:")
            logger.info(f"  Accuracy: {correct}/{total}")
            for r in level_results:
                status = "✓" if r.get("correct") else "✗"
                logger.info(f"    {status} {r['query'][:50]}")

    # Score distribution analysis
    logger.info("\n" + "="*80)
    logger.info("SCORE DISTRIBUTIONS")
    logger.info("="*80)

    all_vector_scores = []
    all_reranker_scores = []

    for r in results:
        if "vector_scores" in r:
            all_vector_scores.extend(r["vector_scores"])
        if "reranker_scores" in r:
            all_reranker_scores.extend(r["reranker_scores"])

    if all_vector_scores:
        logger.info(f"\nVector Scores (Qdrant Cosine Similarity):")
        logger.info(f"  Count: {len(all_vector_scores)}")
        logger.info(f"  Min: {min(all_vector_scores):.4f}")
        logger.info(f"  Max: {max(all_vector_scores):.4f}")
        logger.info(f"  Mean: {sum(all_vector_scores) / len(all_vector_scores):.4f}")

    if all_reranker_scores:
        logger.info(f"\nReranker Scores (MS MARCO Cross-Encoder Logits):")
        logger.info(f"  Count: {len(all_reranker_scores)}")
        logger.info(f"  Min: {min(all_reranker_scores):.4f}")
        logger.info(f"  Max: {max(all_reranker_scores):.4f}")
        logger.info(f"  Mean: {sum(all_reranker_scores) / len(all_reranker_scores):.4f}")

    # Write detailed results to JSON
    output_file = "confidence_calibration_results.json"
    with open(output_file, "w") as f:
        json.dump({
            "settings": {
                "embedding_model": settings.embedding_model,
                "reranker_model": settings.reranker_model,
                "llm_model": settings.llm_model,
                "thresholds": {
                    "reranker": {
                        "high": settings.confidence_high_threshold,
                        "medium": settings.confidence_medium_threshold,
                        "low": settings.confidence_low_threshold,
                    },
                    "vector": {
                        "high": settings.confidence_high_threshold_vector,
                        "medium": settings.confidence_medium_threshold_vector,
                        "low": settings.min_retrieval_score,
                    },
                },
            },
            "test_results": results,
            "accuracy": {
                "correct": correct_count,
                "total": total_count,
                "percentage": accuracy,
            },
            "score_distributions": {
                "vector_scores": {
                    "all": all_vector_scores,
                    "min": min(all_vector_scores) if all_vector_scores else None,
                    "max": max(all_vector_scores) if all_vector_scores else None,
                    "mean": sum(all_vector_scores) / len(all_vector_scores) if all_vector_scores else None,
                },
                "reranker_scores": {
                    "all": all_reranker_scores,
                    "min": min(all_reranker_scores) if all_reranker_scores else None,
                    "max": max(all_reranker_scores) if all_reranker_scores else None,
                    "mean": sum(all_reranker_scores) / len(all_reranker_scores) if all_reranker_scores else None,
                },
            },
        }, f, indent=2)
    logger.info(f"\nDetailed results saved to: {output_file}")


if __name__ == "__main__":
    main()
