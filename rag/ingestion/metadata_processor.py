"""Metadata validation and processing."""

import logging
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class MetadataProcessor:
    """Validates and processes document metadata."""

    REQUIRED_FIELDS = ["department", "category", "version"]
    OPTIONAL_FIELDS = ["date"]

    @staticmethod
    def validate_and_process(
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Validate and normalize metadata.

        Args:
            metadata: User-provided metadata dictionary.

        Returns:
            Validated metadata dictionary with:
            - doc_id: UUID generated
            - department: Normalized lowercase
            - category: Normalized lowercase
            - version: Normalized lowercase
            - date: ISO format or None
            - All original fields preserved

        Raises:
            ValueError: If required fields are missing or invalid.
        """
        logger.debug(f"Processing metadata: {metadata}")

        # Check required fields
        for field in MetadataProcessor.REQUIRED_FIELDS:
            if field not in metadata:
                raise ValueError(f"Missing required metadata field: {field}")

        # Normalize strings
        processed = {}

        for key, value in metadata.items():
            if isinstance(value, str):
                processed[key] = value.strip().lower()
            else:
                processed[key] = value

        # Validate required fields are non-empty after normalization
        for field in MetadataProcessor.REQUIRED_FIELDS:
            if not processed[field]:
                raise ValueError(f"Required field cannot be empty: {field}")

        # Process date
        if "date" in processed and processed["date"]:
            try:
                date_obj = datetime.fromisoformat(str(processed["date"]))
                processed["date"] = date_obj.isoformat()
            except (ValueError, TypeError):
                logger.warning(f"Invalid date format: {processed.get('date')}")
                processed["date"] = None
        else:
            processed["date"] = None

        # Generate doc_id
        processed["doc_id"] = str(uuid4())

        logger.info(f"Metadata validated. doc_id: {processed['doc_id']}")

        return processed
