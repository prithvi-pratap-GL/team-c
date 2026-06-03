"""Qdrant client manager. Frozen contract."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class QdrantClientManager:
    """Qdrant client manager. Frozen ingestion contract.

    Manages connections to Qdrant vector database.
    Collection: enterprise_docs
    Distance: COSINE
    Dimension: 768
    """

    def __init__(
        self,
        url: str = "http://localhost:6333",
        api_key: Optional[str] = None,
    ):
        """Initialize Qdrant client manager.

        Args:
            url: Qdrant server URL. Default: http://localhost:6333
            api_key: Optional Qdrant API key.
        """
        from qdrant_client import QdrantClient

        self.client = QdrantClient(url=url, api_key=api_key)
        self.collection_name = "enterprise_docs"
        logger.info(f"Qdrant client initialized: {url}, collection={self.collection_name}")

    def get_client(self):
        """Get the Qdrant client instance.

        Returns:
            Qdrant client for direct operations.
        """
        return self.client

    def search(self, vector: list[float], limit: int = 10, query_filter=None):
        """Search in enterprise_docs collection.

        Args:
            vector: Query vector (768-dimensional).
            limit: Number of results to return.
            query_filter: Optional Qdrant filter.

        Returns:
            Search results from Qdrant.
        """
        return self.client.search(
            collection_name=self.collection_name,
            query_vector=vector,
            limit=limit,
            query_filter=query_filter,
        )
