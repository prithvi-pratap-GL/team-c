"""Reranker Score Distribution Analysis.

Analyzes actual reranker scores from the database to derive empirical thresholds.

Run with:
    python backend/scripts/analyze_reranker_distribution.py

Output:
    confidence_distribution_report.json
"""

import json
import logging
import sqlite3
import statistics
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent.parent / "rag_backend.db"


def connect_db():
    """Connect to SQLite database."""
    if not DB_PATH.exists():
        logger.error(f"Database not found at {DB_PATH}")
        return None
    return sqlite3.connect(str(DB_PATH))


def get_score_statistics(scores: List[float]) -> Dict:
    """Calculate percentile statistics for a score distribution.

    Args:
        scores: List of numeric scores

    Returns:
        Dict with min, max, mean, median, percentiles
    """
    if not scores:
        return {
            "count": 0,
            "min": None,
            "max": None,
            "mean": None,
            "median": None,
            "p75": None,
            "p90": None,
            "p95": None,
            "p99": None,
        }

    sorted_scores = sorted(scores)
    count = len(scores)

    return {
        "count": count,
        "min": round(min(scores), 4),
        "max": round(max(scores), 4),
        "mean": round(statistics.mean(scores), 4),
        "median": round(statistics.median(scores), 4),
        "p75": round(sorted_scores[int(count * 0.75)], 4),
        "p90": round(sorted_scores[int(count * 0.90)], 4),
        "p95": round(sorted_scores[int(count * 0.95)], 4),
        "p99": round(sorted_scores[int(count * 0.99)], 4),
    }


def analyze_distributions(conn) -> Tuple[Dict, Dict, Dict, Dict]:
    """Analyze score distributions from database.

    Returns:
        Tuple of (vector_stats, reranker_stats, confidence_dist, per_confidence_stats)
    """
    cursor = conn.cursor()

    # Get vector scores (all non-NULL)
    cursor.execute("""
        SELECT vector_score FROM chat_logs
        WHERE vector_score IS NOT NULL
        ORDER BY created_at DESC
    """)
    vector_scores = [row[0] for row in cursor.fetchall()]

    # Get reranker scores (all non-NULL)
    cursor.execute("""
        SELECT reranker_score FROM chat_logs
        WHERE reranker_score IS NOT NULL
        ORDER BY created_at DESC
    """)
    reranker_scores = [row[0] for row in cursor.fetchall()]

    # Get confidence distribution
    cursor.execute("""
        SELECT confidence, COUNT(*) as count
        FROM chat_logs
        GROUP BY confidence
        ORDER BY count DESC
    """)
    confidence_dist = {row[0]: row[1] for row in cursor.fetchall()}

    # Get per-confidence statistics
    per_confidence = {}
    for conf_level in ["high", "medium", "low", "not_found"]:
        cursor.execute("""
            SELECT vector_score, reranker_score FROM chat_logs
            WHERE confidence = ? AND reranker_score IS NOT NULL
            ORDER BY created_at DESC
        """, (conf_level,))
        rows = cursor.fetchall()

        if rows:
            vector_for_conf = [row[0] for row in rows if row[0] is not None]
            reranker_for_conf = [row[1] for row in rows if row[1] is not None]

            per_confidence[conf_level] = {
                "query_count": len(rows),
                "vector_stats": get_score_statistics(vector_for_conf),
                "reranker_stats": get_score_statistics(reranker_for_conf),
            }

    cursor.close()

    vector_stats = get_score_statistics(vector_scores)
    reranker_stats = get_score_statistics(reranker_scores)

    return vector_stats, reranker_stats, confidence_dist, per_confidence


def recommend_thresholds(reranker_stats: Dict, per_confidence: Dict) -> Dict:
    """Generate threshold recommendations based on observed distributions.

    Strategy:
    - HIGH: Use p75 of current HIGH confidence queries
    - MEDIUM: Use p50 (median) as cutoff
    - LOW: Use p25 as cutoff

    Args:
        reranker_stats: Full distribution statistics
        per_confidence: Per-confidence level breakdown

    Returns:
        Dict with recommended thresholds and rationale
    """
    recommendations = {
        "strategy": "percentile-based from observed data",
        "based_on_queries": sum(per_confidence.get(c, {}).get("query_count", 0) for c in per_confidence),
        "note": "Recommendations based on empirical data. Adjust if needed for your knowledge base.",
        "thresholds": {},
        "rationale": {},
    }

    # HIGH threshold: aim for ~20% of queries marked as HIGH
    if per_confidence.get("high", {}).get("reranker_stats"):
        high_p75 = per_confidence["high"]["reranker_stats"]["p75"]
        recommendations["thresholds"]["high"] = high_p75
        recommendations["rationale"]["high"] = (
            f"Set to p75 of current HIGH queries ({high_p75}). "
            "This marks ~20% of results as HIGH (top confidence)."
        )
    else:
        # Fallback: use overall p75
        overall_p75 = reranker_stats["p75"]
        recommendations["thresholds"]["high"] = overall_p75
        recommendations["rationale"]["high"] = (
            f"Fallback to p75 of all reranker scores ({overall_p75}). "
            "Adjust based on HIGH query distribution."
        )

    # MEDIUM threshold: aim for ~50% of queries marked as MEDIUM or better
    if per_confidence.get("medium", {}).get("reranker_stats"):
        medium_p50 = per_confidence["medium"]["reranker_stats"]["p50"]
        recommendations["thresholds"]["medium"] = medium_p50
        recommendations["rationale"]["medium"] = (
            f"Set to p50 of current MEDIUM queries ({medium_p50}). "
            "This marks ~50% of results as MEDIUM or better."
        )
    else:
        # Fallback: use overall median
        overall_median = reranker_stats["median"]
        recommendations["thresholds"]["medium"] = overall_median
        recommendations["rationale"]["medium"] = (
            f"Fallback to median of all reranker scores ({overall_median}). "
            "Adjust based on MEDIUM query distribution."
        )

    # LOW threshold: aim for ~80% of queries marked as LOW or better
    if per_confidence.get("low", {}).get("reranker_stats"):
        low_p25 = per_confidence["low"]["reranker_stats"]["p25"] if "p25" in per_confidence["low"]["reranker_stats"] else per_confidence["low"]["reranker_stats"]["median"]
        recommendations["thresholds"]["low"] = low_p25
        recommendations["rationale"]["low"] = (
            f"Set to p25 of current LOW queries ({low_p25}). "
            "This marks ~80% of results as LOW or better."
        )
    else:
        # Fallback: use overall p25
        sorted_scores = sorted([per_confidence[c]["reranker_stats"]["count"] for c in per_confidence if per_confidence[c]["reranker_stats"]["count"] > 0], reverse=True)
        overall_p25 = reranker_stats.get("p25", reranker_stats["median"] - 1)
        recommendations["thresholds"]["low"] = overall_p25
        recommendations["rationale"]["low"] = (
            f"Fallback to estimated p25 ({overall_p25}). "
            "Adjust based on LOW query distribution."
        )

    recommendations["note"] = (
        "These are data-driven recommendations based on actual observed scores. "
        "Verify they match your expected confidence distribution before deploying."
    )

    return recommendations


def detect_anomalies(per_confidence: Dict) -> List[str]:
    """Detect anomalies in confidence assignment.

    Returns:
        List of warnings if any anomalies detected
    """
    warnings = []

    # Check if HIGH queries have genuinely higher reranker scores
    if per_confidence.get("high") and per_confidence.get("medium"):
        high_mean = per_confidence["high"]["reranker_stats"]["mean"]
        medium_mean = per_confidence["medium"]["reranker_stats"]["mean"]
        if high_mean and medium_mean and high_mean < medium_mean:
            warnings.append(
                f"ANOMALY: HIGH queries have lower mean reranker score ({high_mean}) "
                f"than MEDIUM queries ({medium_mean}). Thresholds may be inverted."
            )

    # Check if LOW queries have the lowest scores
    if per_confidence.get("low") and per_confidence.get("high"):
        low_mean = per_confidence["low"]["reranker_stats"]["mean"]
        high_mean = per_confidence["high"]["reranker_stats"]["mean"]
        if low_mean and high_mean and low_mean > high_mean:
            warnings.append(
                f"ANOMALY: LOW queries have higher mean reranker score ({low_mean}) "
                f"than HIGH queries ({high_mean}). Check confidence logic."
            )

    # Check for missing data
    for level in ["high", "medium", "low", "not_found"]:
        if per_confidence.get(level, {}).get("query_count", 0) == 0:
            warnings.append(f"WARNING: No {level} confidence queries found in database.")

    return warnings


def main():
    """Run reranker distribution analysis."""
    logger.info("\n" + "="*80)
    logger.info("RERANKER DISTRIBUTION ANALYSIS")
    logger.info("="*80)

    conn = connect_db()
    if not conn:
        logger.error("Could not connect to database")
        return

    try:
        logger.info("\nAnalyzing score distributions...")
        vector_stats, reranker_stats, confidence_dist, per_confidence = analyze_distributions(conn)

        logger.info("\nVector Score Distribution (Qdrant Cosine Similarity):")
        logger.info(f"  Count: {vector_stats['count']}")
        logger.info(f"  Range: {vector_stats['min']} to {vector_stats['max']}")
        logger.info(f"  Mean: {vector_stats['mean']}")
        logger.info(f"  Median: {vector_stats['median']}")
        logger.info(f"  P75: {vector_stats['p75']}")
        logger.info(f"  P90: {vector_stats['p90']}")
        logger.info(f"  P95: {vector_stats['p95']}")
        logger.info(f"  P99: {vector_stats['p99']}")

        logger.info("\nReranker Score Distribution (MS MARCO Cross-Encoder):")
        logger.info(f"  Count: {reranker_stats['count']}")
        logger.info(f"  Range: {reranker_stats['min']} to {reranker_stats['max']}")
        logger.info(f"  Mean: {reranker_stats['mean']}")
        logger.info(f"  Median: {reranker_stats['median']}")
        logger.info(f"  P75: {reranker_stats['p75']}")
        logger.info(f"  P90: {reranker_stats['p90']}")
        logger.info(f"  P95: {reranker_stats['p95']}")
        logger.info(f"  P99: {reranker_stats['p99']}")

        logger.info("\nConfidence Distribution (Current Labeling):")
        total_queries = sum(confidence_dist.values())
        for level, count in confidence_dist.items():
            pct = (count / total_queries * 100) if total_queries > 0 else 0
            logger.info(f"  {level.upper()}: {count} ({pct:.1f}%)")

        logger.info("\nPer-Confidence Statistics:")
        for level in ["high", "medium", "low", "not_found"]:
            if per_confidence.get(level):
                info = per_confidence[level]
                logger.info(f"\n  {level.upper()}:")
                logger.info(f"    Queries: {info['query_count']}")
                logger.info(f"    Reranker - Mean: {info['reranker_stats']['mean']}, "
                           f"Median: {info['reranker_stats']['median']}, "
                           f"Range: {info['reranker_stats']['min']} to {info['reranker_stats']['max']}")
                logger.info(f"    Vector - Mean: {info['vector_stats']['mean']}, "
                           f"Median: {info['vector_stats']['median']}, "
                           f"Range: {info['vector_stats']['min']} to {info['vector_stats']['max']}")

        # Generate recommendations
        logger.info("\nGenerating Threshold Recommendations...")
        recommendations = recommend_thresholds(reranker_stats, per_confidence)

        logger.info("\nRECOMMENDED THRESHOLDS:")
        for level, threshold in recommendations["thresholds"].items():
            logger.info(f"  {level.upper()}: {threshold}")
            logger.info(f"    Rationale: {recommendations['rationale'][level]}")

        # Check for anomalies
        anomalies = detect_anomalies(per_confidence)
        if anomalies:
            logger.warning("\nANOMALIES DETECTED:")
            for warning in anomalies:
                logger.warning(f"  ⚠️  {warning}")
        else:
            logger.info("\n✓ No anomalies detected. Confidence distribution looks healthy.")

        # Export results
        report = {
            "analysis_date": datetime.now().isoformat(),
            "query_database": str(DB_PATH),
            "vector_score_distribution": vector_stats,
            "reranker_score_distribution": reranker_stats,
            "confidence_distribution": confidence_dist,
            "per_confidence_statistics": per_confidence,
            "threshold_recommendations": recommendations,
            "anomalies": anomalies,
        }

        report_file = Path(__file__).parent.parent.parent / "confidence_distribution_report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"\n✓ Report saved to: {report_file}")

        logger.info("\n" + "="*80)
        logger.info("ANALYSIS COMPLETE")
        logger.info("="*80)
        logger.info("\nNext Steps:")
        logger.info("1. Review recommended thresholds in confidence_distribution_report.json")
        logger.info("2. Verify thresholds match your expected confidence distribution")
        logger.info("3. Update .env with new thresholds if needed")
        logger.info("4. Monitor actual confidence distribution after deployment")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
