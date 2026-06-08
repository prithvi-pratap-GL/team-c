"""Test to verify the confidence mismatch bug is fixed.

Test case: Reranker score below LOW threshold should map to LOW confidence,
not NOT_FOUND confidence.
"""

import sys
import io
from pathlib import Path

# Fix encoding for Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.models.schemas import Confidence
from app.services.confidence_service import ConfidenceService
from app.config import Settings


def test_negative_reranker_score_maps_to_low():
    """Test that negative reranker scores map to LOW, not NOT_FOUND."""

    service = ConfidenceService()

    # Simulate results with negative reranker score
    test_cases = [
        {
            "name": "Reranker score = -2.0 (below LOW threshold)",
            "reranker_score": -2.0,
            "vector_score": 0.55,
            "expected_confidence": Confidence.low,
            "expected_reason": "reranker_below_low_threshold",
        },
        {
            "name": "Reranker score = -0.5 (slightly below LOW threshold)",
            "reranker_score": -0.5,
            "vector_score": 0.52,
            "expected_confidence": Confidence.low,
            "expected_reason": "reranker_above_low_threshold",  # -0.5 >= -1.0 is true
        },
        {
            "name": "Reranker score = -1.0 (at LOW threshold)",
            "reranker_score": -1.0,
            "vector_score": 0.50,
            "expected_confidence": Confidence.low,
            "expected_reason": "reranker_above_low_threshold",
        },
        {
            "name": "Reranker score = 0.5 (between LOW and MEDIUM)",
            "reranker_score": 0.5,
            "vector_score": 0.58,
            "expected_confidence": Confidence.low,
            "expected_reason": "reranker_above_low_threshold",
        },
        {
            "name": "Reranker score = 1.0 (at MEDIUM threshold)",
            "reranker_score": 1.0,
            "vector_score": 0.62,
            "expected_confidence": Confidence.medium,
            "expected_reason": "reranker_above_medium_threshold",
        },
        {
            "name": "Reranker score = 3.0 (at HIGH threshold)",
            "reranker_score": 3.0,
            "vector_score": 0.68,
            "expected_confidence": Confidence.high,
            "expected_reason": "reranker_above_high_threshold",
        },
    ]

    print("\n" + "="*80)
    print("CONFIDENCE MISMATCH BUG FIX - VERIFICATION TEST")
    print("="*80 + "\n")

    all_passed = True

    for test_case in test_cases:
        # Create mock result with reranker score
        mock_results = [
            {
                "score": test_case["vector_score"],
                "rerank_score": test_case["reranker_score"],
                "chunk_text": "Mock chunk",
                "metadata": {"chunk_id": "test_chunk_1"},
            }
        ]

        # Calculate confidence
        confidence, debug_info = service.calculate(mock_results, has_reranker=True)

        # Check results
        passed = (
            confidence == test_case["expected_confidence"]
            and debug_info.get("reason") == test_case["expected_reason"]
        )

        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_case['name']}")
        print(f"       Reranker Score: {test_case['reranker_score']}")
        print(f"       Expected: {test_case['expected_confidence'].value}")
        print(f"       Got:      {confidence.value}")
        if not passed:
            print(f"       Expected reason: {test_case['expected_reason']}")
            print(f"       Got reason:      {debug_info.get('reason')}")
            all_passed = False
        print()

    print("="*80)
    if all_passed:
        print("✅ ALL TESTS PASSED - BUG FIX VERIFIED")
    else:
        print("❌ SOME TESTS FAILED - BUG FIX INCOMPLETE")
    print("="*80 + "\n")

    return all_passed


def test_no_results_still_returns_not_found():
    """Test that empty results still correctly return NOT_FOUND."""

    service = ConfidenceService()

    # Simulate no results
    mock_results = []

    confidence, debug_info = service.calculate(mock_results, has_reranker=False)

    passed = confidence == Confidence.not_found

    print("\nVERIFY: No results → NOT_FOUND confidence")
    print(f"  Expected: {Confidence.not_found.value}")
    print(f"  Got:      {confidence.value}")
    print(f"  Status:   {'✅ PASS' if passed else '❌ FAIL'}\n")

    return passed


if __name__ == "__main__":
    try:
        test1_passed = test_negative_reranker_score_maps_to_low()
        test2_passed = test_no_results_still_returns_not_found()

        if test1_passed and test2_passed:
            print("\n🎉 ALL VERIFICATION TESTS PASSED")
            print("Bug fix is working correctly!")
            sys.exit(0)
        else:
            print("\n⚠️ SOME TESTS FAILED")
            print("Bug fix may be incomplete")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
