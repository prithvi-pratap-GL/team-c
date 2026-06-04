"""Example usage of the complete RAG pipeline."""

import logging

from app.rag.generation import GroqClientService, PromptBuilder
from app.rag.retrieval import HybridRetriever, MetadataFilterBuilder

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def example_basic_retrieval():
    """Example: Basic vector retrieval."""
    logger.info("=== Example 1: Basic Vector Retrieval ===")

    retriever = HybridRetriever()

    query = "What is the company policy on remote work?"

    try:
        results = retriever.retrieve(query, top_k=5, rerank=False)
        logger.info(f"Retrieved {len(results)} results")

        for idx, result in enumerate(results, 1):
            logger.info(f"Result {idx}:")
            logger.info(f"  Score: {result['score']:.4f}")
            logger.info(f"  Document: {result['metadata']['doc_name']}")
            logger.info(f"  Text: {result['chunk_text'][:100]}...")

    except Exception as e:
        logger.error(f"Retrieval failed: {e}")


def example_retrieval_with_reranking():
    """Example: Vector retrieval with cross-encoder reranking."""
    logger.info("=== Example 2: Vector Retrieval with Reranking ===")

    retriever = HybridRetriever()

    query = "What are the benefits of the company health insurance plan?"

    try:
        results = retriever.retrieve(query, top_k=10, rerank=True, rerank_top_k=3)
        logger.info(f"Retrieved and reranked {len(results)} results")

        for idx, result in enumerate(results, 1):
            logger.info(f"Result {idx}:")
            logger.info(f"  Vector Score: {result['score']:.4f}")
            logger.info(f"  Rerank Score: {result.get('rerank_score', 'N/A')}")
            logger.info(f"  Document: {result['metadata']['doc_name']}")

    except Exception as e:
        logger.error(f"Retrieval failed: {e}")


def example_retrieval_with_filters():
    """Example: Retrieval with metadata filtering."""
    logger.info("=== Example 3: Retrieval with Metadata Filters ===")

    # Note: This example shows filter construction.
    # Actual filtering requires integration with HybridRetriever.
    departments = ["HR", "Engineering"]
    categories = ["Benefits", "Policies"]

    dept_filter = MetadataFilterBuilder.department_filter(departments)
    logger.info(f"Department filter: {dept_filter}")

    cat_filter = MetadataFilterBuilder.category_filter(categories)
    logger.info(f"Category filter: {cat_filter}")

    combined = MetadataFilterBuilder.combined_filter(
        departments=departments,
        categories=categories,
    )
    logger.info(f"Combined filter: {combined}")


def example_end_to_end_pipeline():
    """Example: Complete RAG pipeline from query to generation."""
    logger.info("=== Example 4: End-to-End RAG Pipeline ===")

    retriever = HybridRetriever()
    prompt_builder = PromptBuilder()

    query = "What is the process for requesting time off?"

    try:
        logger.info(f"Query: {query}")

        logger.info("Step 1: Retrieve documents")
        retrieval_results = retriever.retrieve(query, top_k=10, rerank=True, rerank_top_k=5)
        logger.info(f"Retrieved {len(retrieval_results)} results")

        logger.info("Step 2: Build prompts")
        system_prompt, user_prompt = prompt_builder.build_prompt(
            query=query,
            retrieval_results=retrieval_results,
        )
        logger.info(f"System prompt length: {len(system_prompt)}")
        logger.info(f"User prompt: {user_prompt[:100]}...")

        logger.info("Step 3: Generate response (Groq)")
        groq_service = GroqClientService()
        response = groq_service.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.2,
        )
        logger.info(f"Generated response:\n{response}")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")


def example_error_handling():
    """Example: Error handling for invalid inputs."""
    logger.info("=== Example 5: Error Handling ===")

    retriever = HybridRetriever()
    prompt_builder = PromptBuilder()

    logger.info("Testing invalid query...")
    try:
        retriever.retrieve("")
    except ValueError as e:
        logger.info(f"Caught expected error: {e}")

    logger.info("Testing invalid retrieval results...")
    try:
        prompt_builder.build_prompt("Query", "not a list")
    except ValueError as e:
        logger.info(f"Caught expected error: {e}")


if __name__ == "__main__":
    logger.info("RAG Pipeline Examples")
    logger.info("=" * 50)

    # Uncomment to run examples
    # example_basic_retrieval()
    # example_retrieval_with_reranking()
    # example_retrieval_with_filters()
    # example_end_to_end_pipeline()
    # example_error_handling()

    logger.info("Examples defined. Uncomment to run.")
