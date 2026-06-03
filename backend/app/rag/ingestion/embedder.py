"""Embedder using BAAI/bge-base-en-v1.5. Frozen contract."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class Embedder:
    """Embedder using BAAI/bge-base-en-v1.5. Frozen ingestion contract."""

    def __init__(self, model_name: str = "BAAI/bge-base-en-v1.5"):
        """Initialize embedder with BGE model.

        Args:
            model_name: Model identifier. Default: BAAI/bge-base-en-v1.5
        """
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        logger.info(f"Loaded embedder: {model_name}")

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query text.

        Args:
            text: Query text to embed.

        Returns:
            Embedding vector as list of floats.
        """
        embeddings = self.model.encode([text], convert_to_numpy=True)
        return embeddings[0].tolist()

    def embed(self, text: str) -> list[float]:
        """Embed a single text string.

        Args:
            text: Text to embed.

        Returns:
            Embedding vector as list of floats.
        """
        embeddings = self.model.encode([text], convert_to_numpy=True)
        return embeddings[0].tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors.
        """
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return [e.tolist() for e in embeddings]
