"""Reusable Qdrant metadata filters for RBAC and governance."""

import logging
from typing import Optional

from qdrant_client.models import FieldCondition, Filter, MatchAny

logger = logging.getLogger(__name__)


class MetadataFilterBuilder:
    """Builder for composable Qdrant metadata filters."""

    @staticmethod
    def department_filter(departments: list[str]) -> Optional[Filter]:
        """Create a filter for document departments (RBAC).

        Args:
            departments: List of department names to include.

        Returns:
            Qdrant Filter object.
        """
        if not departments:
            logger.warning("Empty departments list provided to department_filter")
            return None

        logger.debug(f"Creating department filter for: {departments}")
        return Filter(
            must=[
                FieldCondition(
                    key="department",
                    match=MatchAny(any=departments),
                )
            ]
        )

    @staticmethod
    def category_filter(categories: list[str]) -> Optional[Filter]:
        """Create a filter for document categories.

        Args:
            categories: List of category names to include.

        Returns:
            Qdrant Filter object.
        """
        if not categories:
            logger.warning("Empty categories list provided to category_filter")
            return None

        logger.debug(f"Creating category filter for: {categories}")
        return Filter(
            must=[
                FieldCondition(
                    key="category",
                    match=MatchAny(any=categories),
                )
            ]
        )

    @staticmethod
    def combined_filter(
        departments: Optional[list[str]] = None,
        categories: Optional[list[str]] = None,
    ) -> Optional[Filter]:
        """Create a combined filter for departments and categories.

        Both conditions are AND-ed together if both are provided.

        Args:
            departments: Optional list of departments to filter by.
            categories: Optional list of categories to filter by.

        Returns:
            Qdrant Filter object or None if no filters provided.
        """
        conditions = []

        if departments:
            logger.debug(f"Adding department condition: {departments}")
            conditions.append(
                FieldCondition(
                    key="department",
                    match=MatchAny(any=departments),
                )
            )

        if categories:
            logger.debug(f"Adding category condition: {categories}")
            conditions.append(
                FieldCondition(
                    key="category",
                    match=MatchAny(any=categories),
                )
            )

        if not conditions:
            logger.debug("No filter conditions provided")
            return None

        logger.debug(f"Creating combined filter with {len(conditions)} conditions")
        return Filter(must=conditions)
