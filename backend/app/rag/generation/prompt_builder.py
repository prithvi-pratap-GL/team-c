"""Prompt construction for hallucination-controlled generation."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Constructs prompts for hallucination-controlled LLM generation."""

    # System prompt enforces strict adherence to provided context
    SYSTEM_PROMPT_TEMPLATE = """You are an Enterprise Knowledge Assistant. Your role is to answer questions based ONLY on the provided context from the knowledge base.

CRITICAL RULES:
1. Answer ONLY using information from the supplied context.
2. Do NOT generate, invent, or hallucinate information not in the context.
3. Do NOT make assumptions beyond what is explicitly stated.
4. If requested information is not in the context, respond exactly with: "I cannot find reliable information in the knowledge base."
5. Always cite your sources by referencing the document names from the context.
6. Be concise and factual.

Provided Context:
{context}"""

    @staticmethod
    def build_context(retrieval_results: list[dict]) -> str:
        """Build formatted context from retrieval results.

        Args:
            retrieval_results: List of retrieval results with metadata.

        Returns:
            Formatted context string.

        Raises:
            ValueError: If results are invalid.
        """
        if not isinstance(retrieval_results, list):
            logger.error(f"Invalid retrieval_results type: {type(retrieval_results)}")
            raise ValueError("retrieval_results must be a list")

        if not retrieval_results:
            logger.warning("Empty retrieval results provided to build_context")
            return "No context available."

        try:
            context_parts = []

            for idx, result in enumerate(retrieval_results, 1):
                if not isinstance(result, dict):
                    logger.warning(f"Skipping non-dict result at index {idx}")
                    continue

                chunk_text = result.get("chunk_text", "")
                metadata = result.get("metadata", {})

                if not chunk_text:
                    logger.debug(f"Skipping result {idx} with empty chunk_text")
                    continue

                doc_name = metadata.get("doc_name", "Unknown Document")
                score = result.get("score", 0)

                context_part = (
                    f"[Document {idx}: {doc_name} (confidence: {score:.2f})]\n"
                    f"{chunk_text}\n"
                )
                context_parts.append(context_part)

            if not context_parts:
                logger.warning("No valid context parts extracted")
                return "No context available."

            context = "\n".join(context_parts)
            logger.debug(f"Built context from {len(context_parts)} results")

            return context

        except Exception as e:
            logger.error(f"Failed to build context: {e}")
            raise

    @staticmethod
    def build_prompt(
        query: str,
        retrieval_results: list[dict],
    ) -> tuple[str, str]:
        """Build system and user prompts for generation.

        Args:
            query: User query.
            retrieval_results: List of retrieval results.

        Returns:
            Tuple of (system_prompt, user_prompt).

        Raises:
            ValueError: If inputs are invalid.
        """
        if not query or not isinstance(query, str) or query.strip() == "":
            logger.error(f"Invalid query: {query}")
            raise ValueError("Query must be a non-empty string")

        if not isinstance(retrieval_results, list):
            logger.error(f"Invalid retrieval_results type: {type(retrieval_results)}")
            raise ValueError("retrieval_results must be a list")

        try:
            context = PromptBuilder.build_context(retrieval_results)

            system_prompt = PromptBuilder.SYSTEM_PROMPT_TEMPLATE.format(context=context)

            user_prompt = f"Question: {query}\n\nPlease answer based only on the provided context."

            logger.debug("Built generation prompts")

            return system_prompt, user_prompt

        except ValueError as e:
            logger.error(f"Validation error in build_prompt: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to build prompts: {e}")
            raise
