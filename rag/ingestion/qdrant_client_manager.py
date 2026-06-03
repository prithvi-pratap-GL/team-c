"""Qdrant client initialization and collection management."""

import logging
from typing import Optional

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

logger = logging.getLogger(__name__)


class QdrantClientManager:
    """Manages Qdrant client lifecycle and collection initialization."""

    _instance: Optional["QdrantClientManager"] = None
    _client: Optional[QdrantClient] = None

    COLLECTION_NAME = "enterprise_docs"
    VECTOR_SIZE = 768
    DISTANCE_METRIC = Distance.COSINE

    def __new__(cls) -> "QdrantClientManager":
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, url: str = "http://localhost:6333") -> None:
        """Initialize Qdrant client.

        Args:
            url: Qdrant server URL. Defaults to localhost.
        """
        if self._client is None:
            logger.info(f"Initializing Qdrant client at {url}")
            self._client = QdrantClient(url=url)
            self._url = url

    def get_client(self) -> QdrantClient:
        """Get or create Qdrant client.

        Returns:
            QdrantClient instance.
        """
        if self._client is None:
            self.__init__()
        return self._client

    def create_collection(self) -> None:
        """Create collection if it doesn't exist.

        Collection is configured with:
        - Vector size: 768 (BAAI/bge-base-en-v1.5)
        - Distance metric: COSINE
        - Name: enterprise_docs
        """
        client = self.get_client()

        try:
            client.get_collection(self.COLLECTION_NAME)
            logger.info(f"Collection '{self.COLLECTION_NAME}' already exists")
        except Exception as e:
            logger.info(f"Creating collection '{self.COLLECTION_NAME}'")
            client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=self.VECTOR_SIZE,
                    distance=self.DISTANCE_METRIC,
                ),
            )
            logger.info(f"Collection '{self.COLLECTION_NAME}' created successfully")

    def health_check(self) -> bool:
        """Check if Qdrant server is healthy.

        Returns:
            True if server is accessible, False otherwise.
        """
        try:
            client = self.get_client()
            client.get_collections()
            logger.info("Qdrant health check passed")
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False
