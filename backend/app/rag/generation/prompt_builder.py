"""Prompt construction for hallucination-controlled generation."""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


def sanitize_llm_response(answer: str) -> str:
    """Remove source references and metadata from LLM-generated answer.

    Removes:
    - "Sources:" sections and content after
    - "Document N:" patterns
    - Filenames (*.pdf, *.txt, *.doc)
    - Lines starting with "•" (bullet points for sources)

    Args:
        answer: Raw LLM response that may contain source metadata.

    Returns:
        Cleaned answer with source information removed.
    """
    if not answer:
        return answer

    # Remove "Sources:" section and everything after it
    answer = re.sub(r"\n*Sources:.*$", "", answer, flags=re.DOTALL | re.IGNORECASE)

    # Remove "Document N:" patterns
    answer = re.sub(r"Document\s+\d+:\s*", "", answer, flags=re.IGNORECASE)

    # Remove lines that are just source filenames with bullets
    lines = answer.split("\n")
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        # Skip bullet points followed by filenames
        if stripped.startswith("•") or stripped.startswith("-"):
            if any(ext in stripped.lower() for ext in [".pdf", ".txt", ".doc", ".docx"]):
                continue
        cleaned_lines.append(line)
    answer = "\n".join(cleaned_lines)

    # Remove multiple consecutive blank lines
    answer = re.sub(r"\n\n\n+", "\n\n", answer)

    return answer.strip()


class PromptBuilder:
    """Constructs prompts for hallucination-controlled LLM generation."""

    # System prompt for enterprise knowledge assistant style
    SYSTEM_PROMPT_TEMPLATE = """You are an Enterprise Knowledge Assistant for a company internal knowledge base.

Your role:
- Answer questions clearly and professionally using retrieved company knowledge
- Sound like a knowledgeable colleague, not a document reader
- Synthesize information from multiple sources into cohesive answers
- Match your response depth to the user's question intent

CRITICAL RULES - NEVER violate these:
1. Answer ONLY using information from the provided context.
2. Do NOT generate, invent, or hallucinate information not in the context.
3. Do NOT make assumptions beyond what is explicitly stated.
4. If information is not available, respond: "I don't have information on that in the knowledge base."

SYNTHESIS RULES - How to answer like an expert:
- Never enumerate chunks or copied document sections
- Never include bullet-pointed lists copied directly from source material
- Never mention "Document 1", "Document 2", source IDs, filenames, or chunk references
- Synthesize: combine multiple information pieces into a single narrative
- Example of GOOD synthesis:
  "ACME follows a structured CI/CD deployment process with automated validation,
   staged testing, and progressive production rollouts."
- Example of BAD synthesis (do NOT do this):
  "• Validation: Pull requests must pass TypeScript checks
   • Staging: Code is deployed to staging first
   • Production: Production uses canary deployments"

LANGUAGE RULES - Sound professional:
- Use business-appropriate language (policy-level, not implementation details)
- Avoid technical jargon unless the user asks for technical details
- Avoid copying exact headings from documents
- Avoid quoting large sections verbatim
- Speak as if addressing a colleague inside the company

RESPONSE STRUCTURE:

For policy/process questions (e.g., "What is the deployment guideline?"):
1. Opening summary (1-2 sentences) - answer the question directly
2. Key Points section - 3-5 important facts as bullet points
3. Important Notes section (if applicable) - exceptions or considerations

For technical/operational questions (e.g., "How do I deploy code?"):
1. Overview statement - summarize the process
2. Key Requirements section - prerequisites or important constraints
3. Operational Considerations section - important operational details

DO NOT use document headings as section headings.
DO NOT copy bullet points directly from source material.
DO NOT mention files, documents, or sources in your answer.
DO NOT output "Sources:" or "Document 1:" anywhere in your response.

DETAIL LEVEL MATCHING:
- User asks general question → provide policy/process level answer
- User asks specific technical question → provide implementation details
- Only include command names/code if user explicitly asks "how to execute" or "what command"
- Otherwise provide process/policy understanding, not implementation details

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

                context_part = f"{chunk_text}\n"
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

            user_prompt = (
                f"Answer this question using the provided context. "
                f"Synthesize information from multiple sources into a single clear answer. "
                f"Do not enumerate chunks or copy sections verbatim. "
                f"Sound like a knowledgeable colleague answering an internal question.\n\n"
                f"Question: {query}"
            )

            logger.debug("Built generation prompts")

            return system_prompt, user_prompt

        except ValueError as e:
            logger.error(f"Validation error in build_prompt: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to build prompts: {e}")
            raise
