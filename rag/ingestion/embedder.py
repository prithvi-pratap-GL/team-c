"""Document embedding service."""

import logging
from typing import List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class Embedder:
    """Embedding service using sentence-transformers."""

    MODEL_NAME = "BAAI/bge-base-en-v1.5"
    EMBEDDING_DIMENSION = 768

    _instance: Optional["Embedder"] = None
    _model: Optional[SentenceTransformer] = None

    def __new__(cls) -> "Embedder":
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize embedder with model."""
        if self._model is None:
            logger.info(f"Loading embedding model: {self.MODEL_NAME}")
            self._model = SentenceTransformer(self.MODEL_NAME)
            logger.info(f"Model loaded. Embedding dimension: {self.EMBEDDING_DIMENSION}")

    def embed_chunks(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Embed multiple text chunks.

        Args:
            texts: List of text chunks to embed.
            batch_size: Batch size for embedding. Defaults to 32.

        Returns:
            List of embedding vectors (768-dimensional).

        Raises:
            ValueError: If texts is empty.
        """
        if not texts:
            raise ValueError("Cannot embed empty text list")

        logger.info(f"Embedding {len(texts)} chunks (batch_size={batch_size})")

        embeddings = self._model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
        )

        embeddings_list = [embedding.tolist() for embedding in embeddings]
        logger.info(f"Successfully embedded {len(embeddings_list)} chunks")

        return embeddings_list

    def embed_query(self, query: str) -> List[float]:
        """Embed a single query string.

        Args:
            query: Query text to embed.

        Returns:
            Single embedding vector (768-dimensional).

        Raises:
            ValueError: If query is empty.
        """
        if not query or not query.strip():
            raise ValueError("Cannot embed empty query")

        logger.debug(f"Embedding query: {query[:100]}...")

        embedding = self._model.encode(query, show_progress_bar=False)

        return embedding.tolist()

    def get_dimension(self) -> int:
        """Get embedding dimension.

        Returns:
            Embedding vector dimension (768).
        """
        return self.EMBEDDING_DIMENSION
