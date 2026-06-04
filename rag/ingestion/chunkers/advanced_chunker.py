"""Advanced section-aware chunking strategy."""

import logging
from typing import Any, Dict, List
from uuid import uuid4

from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


class AdvancedChunker:
    """Section-aware chunking using custom separators."""

    SEPARATORS = [
        "\n\n",
        "\n",
        ". ",
        " ",
    ]

    def __init__(self) -> None:
        """Initialize advanced chunker."""
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=512,
            chunk_overlap=64,
            separators=self.SEPARATORS,
        )
        logger.info(
            f"Initialized AdvancedChunker with separators: {self.SEPARATORS}"
        )

    def chunk(self, text: str) -> List[Dict[str, Any]]:
        """Chunk text using section-aware strategy.

        Respects document structure by preferring paragraph, line,
        and sentence breaks over character splits.

        Args:
            text: Document text to chunk.

        Returns:
            List of chunks, each with:
            - chunk_id: UUID
            - chunk_text: Chunk content
        """
        logger.debug(f"Chunking text with AdvancedChunker (length: {len(text)})")

        chunks_text = self.splitter.split_text(text)
        chunks = [
            {
                "chunk_id": str(uuid4()),
                "chunk_text": chunk_text,
            }
            for chunk_text in chunks_text
        ]

        logger.info(f"Created {len(chunks)} advanced chunks")
        return chunks
