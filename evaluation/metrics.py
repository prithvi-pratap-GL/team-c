"""
Evaluation metrics for RAG system performance

Scoring approach:
- 3: Correct answer, correct source doc cited
- 2: Correct answer, wrong/missing source
- 1: Partially correct
- 0: Wrong or hallucinated

MRR (Mean Reciprocal Rank): Inverse of the rank of the first relevant document
"""
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class EvaluationQuery:
    """Evaluation query with expected results"""
    query_number: int
    query_text: str
    expected_department: str
    expected_doc_type: str


@dataclass
class RetrievalResult:
    """Result from a retrieval operation"""
    doc_id: str
    doc_name: str
    score: float
    rank: int


class Metrics:
    """Calculate evaluation metrics"""

    @staticmethod
    def mrr(relevant_ranks: List[int]) -> float:
        """
        Mean Reciprocal Rank - position of first relevant document
        Higher is better (1.0 = first result, 0.5 = second result)
        """
        if not relevant_ranks:
            return 0.0
        return 1.0 / relevant_ranks[0]

    @staticmethod
    def hit_in_top_k(relevant_ranks: List[int], k: int = 5) -> bool:
        """Check if any relevant result in top k"""
        if not relevant_ranks:
            return False
        return relevant_ranks[0] <= k

    @staticmethod
    def recall_at_k(relevant_count: int, retrieved_count: int, k: int = 5) -> float:
        """Recall@k - fraction of relevant docs retrieved in top k"""
        if relevant_count == 0:
            return 0.0
        return min(retrieved_count, k) / relevant_count

    @staticmethod
    def ndcg(scores: List[float], k: int = 5) -> float:
        """
        Normalized Discounted Cumulative Gain
        Considers rank and relevance score
        """
        if not scores:
            return 0.0

        dcg = sum((2 ** score - 1) / (i + 2) for i, score in enumerate(scores[:k]))
        idcg = sum((2 ** score - 1) / (i + 2) for i, score in enumerate(sorted(scores, reverse=True)[:k]))

        return dcg / idcg if idcg > 0 else 0.0


# Evaluation queries from blueprint
EVALUATION_QUERIES = [
    EvaluationQuery(
        query_number=1,
        query_text="What is the annual leave entitlement?",
        expected_department="hr",
        expected_doc_type="policy"
    ),
    EvaluationQuery(
        query_number=2,
        query_text="How do I rollback a failed deployment?",
        expected_department="engineering",
        expected_doc_type="guide"
    ),
    EvaluationQuery(
        query_number=3,
        query_text="What are the SLA tiers for incident escalation?",
        expected_department="operations",
        expected_doc_type="policy"
    ),
    EvaluationQuery(
        query_number=4,
        query_text="How do I reset a user password?",
        expected_department="product_support",
        expected_doc_type="faq"
    ),
    EvaluationQuery(
        query_number=5,
        query_text="What changed in release 2.4.0?",
        expected_department="engineering",
        expected_doc_type="release_notes"
    ),
    EvaluationQuery(
        query_number=6,
        query_text="What is the parental leave policy?",
        expected_department="hr",
        expected_doc_type="policy"
    ),
    EvaluationQuery(
        query_number=7,
        query_text="INC-2024-003: what was the root cause?",
        expected_department="operations",
        expected_doc_type="incident"
    ),
    EvaluationQuery(
        query_number=8,
        query_text="How is overtime calculated?",
        expected_department="hr",
        expected_doc_type="policy"
    ),
    EvaluationQuery(
        query_number=9,
        query_text="What ports does the API gateway expose?",
        expected_department="engineering",
        expected_doc_type="guide"
    ),
    EvaluationQuery(
        query_number=10,
        query_text="How long are support tickets retained?",
        expected_department="product_support",
        expected_doc_type="policy"
    ),
]
