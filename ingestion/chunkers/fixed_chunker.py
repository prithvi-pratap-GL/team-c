"""Fixed-size chunking strategy."""

import logging
from typing import Any, Dict, List
from uuid import uuid4

from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


class FixedChunker:
    """Fixed-size chunking using RecursiveCharacterTextSplitter."""

    CHUNK_SIZE = 512
    CHUNK_OVERLAP = 64

    def __init__(self) -> None:
        """Initialize fixed chunker."""
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.CHUNK_SIZE,
            chunk_overlap=self.CHUNK_OVERLAP,
        )
        logger.info(
            f"Initialized FixedChunker: "
            f"size={self.CHUNK_SIZE}, overlap={self.CHUNK_OVERLAP}"
        )

    def chunk(self, text: str) -> List[Dict[str, Any]]:
        """Chunk text into fixed-size pieces.

        Args:
            text: Document text to chunk.

        Returns:
            List of chunks, each with:
            - chunk_id: UUID
            - chunk_text: Chunk content
        """
        logger.debug(f"Chunking text with FixedChunker (length: {len(text)})")

        chunks_text = self.splitter.split_text(text)
        chunks = [
            {
                "chunk_id": str(uuid4()),
                "chunk_text": chunk_text,
            }
            for chunk_text in chunks_text
        ]

        logger.info(f"Created {len(chunks)} fixed-size chunks")
        return chunks
