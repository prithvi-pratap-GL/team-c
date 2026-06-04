"""Plain text document parser."""

import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


class TxtParser:
    """Parser for plain text documents."""

    @staticmethod
    def parse(file_path: str) -> Dict[str, Any]:
        """Parse text file with UTF-8 encoding.

        Args:
            file_path: Path to text file.

        Returns:
            Dictionary containing:
            - text: Full file content
            - document_type: 'txt'
            - metadata: Dict with filename

        Raises:
            FileNotFoundError: If file does not exist.
            ValueError: If file cannot be decoded as UTF-8.
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Text file not found: {file_path}")

        if path.suffix.lower() != ".txt":
            raise ValueError(f"File is not a text file: {file_path}")

        try:
            logger.info(f"Parsing text file: {file_path}")
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()

            if not text.strip():
                logger.warning(f"Text file {file_path} is empty")

            logger.info(f"Successfully parsed text file")

            return {
                "text": text,
                "document_type": "txt",
                "metadata": {
                    "filename": path.name,
                },
            }

        except UnicodeDecodeError as e:
            logger.error(f"Error decoding text file {file_path}: {e}")
            raise ValueError(f"File is not UTF-8 encoded: {e}")
        except Exception as e:
            logger.error(f"Error parsing text file {file_path}: {e}")
            raise ValueError(f"Failed to parse text file: {e}")
