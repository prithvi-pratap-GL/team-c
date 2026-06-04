"""PDF document parser."""

import logging
from pathlib import Path
from typing import Any, Dict

from pypdf import PdfReader

logger = logging.getLogger(__name__)


class PDFParser:
    """Parser for PDF documents."""

    @staticmethod
    def parse(file_path: str) -> Dict[str, Any]:
        """Parse PDF file and extract text.

        Args:
            file_path: Path to PDF file.

        Returns:
            Dictionary containing:
            - text: Full extracted text from PDF
            - document_type: 'pdf'
            - metadata: Dict with filename and page_count

        Raises:
            FileNotFoundError: If file does not exist.
            ValueError: If file is not a valid PDF.
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        if path.suffix.lower() != ".pdf":
            raise ValueError(f"File is not a PDF: {file_path}")

        try:
            logger.info(f"Parsing PDF: {file_path}")
            reader = PdfReader(file_path)
            page_count = len(reader.pages)

            text_parts = []
            for page_num, page in enumerate(reader.pages, 1):
                text = page.extract_text()
                if text:
                    text_parts.append(text)

            full_text = "\n".join(text_parts)

            if not full_text.strip():
                logger.warning(f"PDF {file_path} contains no extractable text")

            logger.info(f"Successfully parsed PDF with {page_count} pages")

            return {
                "text": full_text,
                "document_type": "pdf",
                "metadata": {
                    "filename": path.name,
                    "page_count": page_count,
                },
            }

        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {e}")
            raise ValueError(f"Failed to parse PDF: {e}")
