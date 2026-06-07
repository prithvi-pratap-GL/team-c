"""Qdrant client initialization and collection management."""

import logging
import os
from typing import Optional
from dotenv import load_dotenv

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, KeywordIndexParams, KeywordIndexType

load_dotenv()

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

    def __init__(self,url: Optional[str] = None,api_key: Optional[str]=None) -> None:
        """Initialize Qdrant client.

        Args:
            url: Qdrant server URL. Defaults to localhost.
        """
        if self._client is None:
            if url is None:
                url = os.getenv("QDRANT_URL")

            if api_key is None:
                api_key = os.getenv("QDRANT_API_KEY")

            logger.info(f"Initializing Qdrant client at {url}")

            self._client = QdrantClient(
                url=url,
                api_key=api_key,
            )

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
        - Payload indexes: department, category, document_type, doc_name
        """
        client = self.get_client()

        try:
            client.get_collection(self.COLLECTION_NAME)
            logger.info(f"Collection '{self.COLLECTION_NAME}' already exists")
            # Ensure payload indexes exist (migrate if needed)
            self._ensure_payload_indexes(client)
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
            # Create payload indexes for filtering
            self._ensure_payload_indexes(client)

    def _ensure_payload_indexes(self, client: QdrantClient) -> None:
        """Ensure required payload indexes exist for filtering.

        Creates keyword indexes for:
        - department: RBAC filtering
        - category: Category-based filtering
        - document_type: Document type filtering
        - doc_name: Document name filtering

        Args:
            client: QdrantClient instance
        """
        fields_to_index = [
            "department",
            "category",
            "document_type",
            "doc_name",
        ]

        for field_name in fields_to_index:
            try:
                client.create_payload_index(
                    collection_name=self.COLLECTION_NAME,
                    field_name=field_name,
                    field_schema=KeywordIndexParams(
                        type=KeywordIndexType.KEYWORD,
                    ),
                )
                logger.info(
                    f"Payload index created/verified for field '{field_name}' "
                    f"in collection '{self.COLLECTION_NAME}'"
                )
            except Exception as e:
                logger.debug(
                    f"Index for field '{field_name}' may already exist: {e}"
                )

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
