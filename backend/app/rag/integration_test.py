"""Integration tests for the complete RAG pipeline."""

import logging
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def test_vector_retriever():
    """Test VectorRetriever module."""
    logger.info("=" * 60)
    logger.info("TEST: VectorRetriever")
    logger.info("=" * 60)

    from rag.retrieval.vector_retriever import VectorRetriever, QdrantClientManager, Embedder

    try:
        embedder = Embedder()
        logger.info("✓ Embedder initialized successfully")

        vector = embedder.embed("test query")
        logger.info(f"✓ Embedding generated, dimension: {len(vector)}")
        assert len(vector) == 768, "Embedding dimension should be 768"

        batch_vectors = embedder.embed_batch(["query 1", "query 2"])
        logger.info(f"✓ Batch embedding generated: {len(batch_vectors)} vectors")
        assert len(batch_vectors) == 2

    except Exception as e:
        logger.error(f"✗ Embedder test failed: {e}")
        return False

    try:
        retriever = VectorRetriever()
        logger.info("✓ VectorRetriever initialized successfully")

        try:
            retriever.retrieve("")
            logger.error("✗ Should have raised ValueError for empty query")
            return False
        except ValueError:
            logger.info("✓ Correctly rejected empty query")

        try:
            retriever.retrieve(None)
            logger.error("✗ Should have raised ValueError for None query")
            return False
        except ValueError:
            logger.info("✓ Correctly rejected None query")

        logger.info("✓ Input validation working correctly")
        return True

    except Exception as e:
        logger.error(f"✗ VectorRetriever test failed: {e}")
        return False


def test_metadata_filter():
    """Test MetadataFilterBuilder module."""
    logger.info("=" * 60)
    logger.info("TEST: MetadataFilterBuilder")
    logger.info("=" * 60)

    from rag.retrieval.metadata_filter import MetadataFilterBuilder

    try:
        dept_filter = MetadataFilterBuilder.department_filter(["HR", "Engineering"])
        logger.info(f"✓ Department filter created: {dept_filter}")
        assert dept_filter is not None
        assert "must" in dept_filter

        cat_filter = MetadataFilterBuilder.category_filter(["Benefits"])
        logger.info(f"✓ Category filter created: {cat_filter}")
        assert cat_filter is not None

        combined = MetadataFilterBuilder.combined_filter(
            departments=["HR"],
            categories=["Policies"],
        )
        logger.info(f"✓ Combined filter created with 2 conditions")
        assert len(combined["must"]) == 2

        empty_combined = MetadataFilterBuilder.combined_filter()
        logger.info(f"✓ Empty filter returned None: {empty_combined is None}")
        assert empty_combined is None

        return True

    except Exception as e:
        logger.error(f"✗ MetadataFilterBuilder test failed: {e}")
        return False


def test_reranker():
    """Test Reranker module."""
    logger.info("=" * 60)
    logger.info("TEST: Reranker")
    logger.info("=" * 60)

    from rag.retrieval.rerankers import Reranker, get_reranker

    try:
        reranker1 = Reranker()
        reranker2 = get_reranker()
        logger.info(f"✓ Reranker initialized (singleton: {reranker1 is reranker2})")
        assert reranker1 is reranker2, "Should be singleton"

        try:
            reranker1.rerank("", [])
            logger.error("✗ Should have raised ValueError for empty query")
            return False
        except ValueError:
            logger.info("✓ Correctly rejected empty query")

        try:
            reranker1.rerank("query", "not a list")
            logger.error("✗ Should have raised ValueError for non-list results")
            return False
        except ValueError:
            logger.info("✓ Correctly rejected non-list results")

        logger.info("✓ Input validation working correctly")
        return True

    except Exception as e:
        logger.error(f"✗ Reranker test failed: {e}")
        return False


def test_hybrid_retriever():
    """Test HybridRetriever module."""
    logger.info("=" * 60)
    logger.info("TEST: HybridRetriever")
    logger.info("=" * 60)

    from rag.retrieval.hybrid_retriever import HybridRetriever

    try:
        retriever = HybridRetriever()
        logger.info("✓ HybridRetriever initialized successfully")

        try:
            retriever.retrieve("")
            logger.error("✗ Should have raised ValueError for empty query")
            return False
        except ValueError:
            logger.info("✓ Correctly rejected empty query")

        logger.info("✓ Input validation working correctly")
        return True

    except Exception as e:
        logger.error(f"✗ HybridRetriever test failed: {e}")
        return False


def test_groq_client():
    """Test GroqClientService module."""
    logger.info("=" * 60)
    logger.info("TEST: GroqClientService")
    logger.info("=" * 60)

    from rag.generation.groq_client import GroqClientService

    try:
        try:
            groq = GroqClientService()
            logger.info("✓ GroqClientService initialized (using env GROQ_API_KEY)")
        except ValueError as e:
            logger.info(f"⚠ GroqClientService requires GROQ_API_KEY environment variable")
            logger.info(f"  Error: {e}")
            return True  # Expected when no API key

        try:
            groq.generate("", "")
            logger.error("✗ Should have raised ValueError for empty prompts")
            return False
        except ValueError:
            logger.info("✓ Correctly rejected empty prompts")

        try:
            groq.generate("system", "user", temperature=3.0)
            logger.error("✗ Should have raised ValueError for invalid temperature")
            return False
        except ValueError:
            logger.info("✓ Correctly rejected invalid temperature")

        return True

    except Exception as e:
        logger.error(f"✗ GroqClientService test failed: {e}")
        return False


def test_prompt_builder():
    """Test PromptBuilder module."""
    logger.info("=" * 60)
    logger.info("TEST: PromptBuilder")
    logger.info("=" * 60)

    from rag.generation.prompt_builder import PromptBuilder

    try:
        pb = PromptBuilder()
        logger.info("✓ PromptBuilder initialized successfully")

        try:
            pb.build_context("not a list")
            logger.error("✗ Should have raised ValueError for non-list results")
            return False
        except ValueError:
            logger.info("✓ Correctly rejected non-list results")

        context = pb.build_context([])
        logger.info(f"✓ Empty results handled: '{context}'")
        assert "No context available" in context

        sample_results = [
            {
                "score": 0.95,
                "chunk_text": "This is sample text.",
                "metadata": {
                    "doc_name": "Sample Document",
                    "chunk_id": "chunk_1",
                },
            }
        ]

        context = pb.build_context(sample_results)
        logger.info(f"✓ Context built with {len(context)} characters")
        assert "Sample Document" in context
        assert "This is sample text" in context

        try:
            pb.build_prompt("", sample_results)
            logger.error("✗ Should have raised ValueError for empty query")
            return False
        except ValueError:
            logger.info("✓ Correctly rejected empty query")

        system, user = pb.build_prompt("What is this?", sample_results)
        logger.info(f"✓ Prompts built: system={len(system)} chars, user={len(user)} chars")
        assert "What is this?" in user
        assert "Enterprise Knowledge Assistant" in system

        return True

    except Exception as e:
        logger.error(f"✗ PromptBuilder test failed: {e}")
        return False


def test_imports():
    """Test all imports and module structure."""
    logger.info("=" * 60)
    logger.info("TEST: Module Imports")
    logger.info("=" * 60)

    try:
        from rag.retrieval import (
            VectorRetriever,
            MetadataFilterBuilder,
            Reranker,
            get_reranker,
            HybridRetriever,
        )
        logger.info("✓ All retrieval modules imported successfully")

        from rag.generation import GroqClientService, PromptBuilder
        logger.info("✓ All generation modules imported successfully")

        assert VectorRetriever is not None
        assert MetadataFilterBuilder is not None
        assert Reranker is not None
        assert get_reranker is not None
        assert HybridRetriever is not None
        assert GroqClientService is not None
        assert PromptBuilder is not None

        logger.info("✓ All imports verified")
        return True

    except Exception as e:
        logger.error(f"✗ Import test failed: {e}")
        return False


def run_all_tests():
    """Run all integration tests."""
    logger.info("=" * 60)
    logger.info("RAG PIPELINE INTEGRATION TESTS")
    logger.info("=" * 60)
    logger.info("")

    tests = [
        ("Module Imports", test_imports),
        ("VectorRetriever", test_vector_retriever),
        ("MetadataFilterBuilder", test_metadata_filter),
        ("Reranker", test_reranker),
        ("HybridRetriever", test_hybrid_retriever),
        ("PromptBuilder", test_prompt_builder),
        ("GroqClientService", test_groq_client),
    ]

    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            logger.error(f"Unexpected error in {name}: {e}")
            results[name] = False
        logger.info("")

    logger.info("=" * 60)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status:8} | {name}")

    logger.info("=" * 60)
    logger.info(f"Results: {passed}/{total} tests passed")
    logger.info("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
