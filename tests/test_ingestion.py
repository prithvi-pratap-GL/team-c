"""Test suite for ingestion pipeline."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rag.ingestion import (
    AdvancedChunker,
    Embedder,
    FixedChunker,
    IngestPipeline,
    MetadataProcessor,
    PDFParser,
    TxtParser,
)


class TestPDFParser:
    """Test PDF parsing."""

    def test_parse_pdf_file_not_found(self):
        """Test error when PDF file not found."""
        with pytest.raises(FileNotFoundError):
            PDFParser.parse("/nonexistent/file.pdf")

    def test_parse_invalid_pdf_extension(self):
        """Test error for non-PDF file."""
        with tempfile.NamedTemporaryFile(suffix=".txt") as tmp:
            with pytest.raises(ValueError):
                PDFParser.parse(tmp.name)

    @patch("rag.ingestion.parsers.pdf_parser.PdfReader")
    def test_parse_pdf_success(self, mock_pdf_reader):
        """Test successful PDF parsing."""
        mock_reader = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Sample PDF content"
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            try:
                result = PDFParser.parse(tmp.name)

                assert result["document_type"] == "pdf"
                assert result["text"] == "Sample PDF content"
                assert result["metadata"]["page_count"] == 1
            finally:
                try:
                    Path(tmp.name).unlink()
                except (PermissionError, OSError):
                    pass


class TestTxtParser:
    """Test text file parsing."""

    def test_parse_txt_file_not_found(self):
        """Test error when text file not found."""
        with pytest.raises(FileNotFoundError):
            TxtParser.parse("/nonexistent/file.txt")

    def test_parse_invalid_txt_extension(self):
        """Test error for non-TXT file."""
        with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
            with pytest.raises(ValueError):
                TxtParser.parse(tmp.name)

    def test_parse_txt_success(self):
        """Test successful text file parsing."""
        content = "This is sample text content\nWith multiple lines"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(content)
            tmp.flush()

            try:
                result = TxtParser.parse(tmp.name)

                assert result["document_type"] == "txt"
                assert result["text"] == content
                assert "filename" in result["metadata"]
            finally:
                try:
                    Path(tmp.name).unlink()
                except (PermissionError, OSError):
                    pass


class TestMetadataProcessor:
    """Test metadata validation and processing."""

    def test_missing_required_field(self):
        """Test error when required field is missing."""
        metadata = {
            "department": "engineering",
            "category": "technical",
        }

        with pytest.raises(ValueError, match="Missing required metadata field"):
            MetadataProcessor.validate_and_process(metadata)

    def test_empty_required_field(self):
        """Test error when required field is empty."""
        metadata = {
            "department": "engineering",
            "category": "technical",
            "version": "",
        }

        with pytest.raises(ValueError, match="Required field cannot be empty"):
            MetadataProcessor.validate_and_process(metadata)

    def test_normalize_metadata(self):
        """Test metadata normalization."""
        metadata = {
            "department": "  ENGINEERING  ",
            "category": "TECHNICAL",
            "version": "V1.0",
            "date": "2024-01-15",
        }

        result = MetadataProcessor.validate_and_process(metadata)

        assert result["department"] == "engineering"
        assert result["category"] == "technical"
        assert result["version"] == "v1.0"
        assert "doc_id" in result
        assert result["date"] == "2024-01-15T00:00:00"

    def test_invalid_date_format(self):
        """Test handling of invalid date format."""
        metadata = {
            "department": "engineering",
            "category": "technical",
            "version": "1.0",
            "date": "invalid-date",
        }

        result = MetadataProcessor.validate_and_process(metadata)

        assert result["date"] is None


class TestChunkers:
    """Test chunking strategies."""

    def test_fixed_chunker_basic(self):
        """Test fixed chunker produces chunks."""
        chunker = FixedChunker()
        text = "This is a sample document. " * 50

        chunks = chunker.chunk(text)

        assert len(chunks) > 0
        assert all("chunk_id" in c for c in chunks)
        assert all("chunk_text" in c for c in chunks)

    def test_advanced_chunker_basic(self):
        """Test advanced chunker produces chunks."""
        chunker = AdvancedChunker()
        text = "This is a sample document.\n\nWith paragraphs.\n\nAnd more content."

        chunks = chunker.chunk(text)

        assert len(chunks) > 0
        assert all("chunk_id" in c for c in chunks)
        assert all("chunk_text" in c for c in chunks)

    def test_chunkers_different_output(self):
        """Test that different strategies may produce different chunking."""
        text = "This is a test. " * 30

        fixed_chunker = FixedChunker()
        advanced_chunker = AdvancedChunker()

        fixed_chunks = fixed_chunker.chunk(text)
        advanced_chunks = advanced_chunker.chunk(text)

        # Both should produce chunks
        assert len(fixed_chunks) > 0
        assert len(advanced_chunks) > 0


class TestEmbedder:
    """Test embedding service."""

    def test_embedder_singleton(self):
        """Test embedder singleton pattern."""
        embedder1 = Embedder()
        embedder2 = Embedder()

        assert embedder1 is embedder2

    @pytest.mark.integration
    def test_embed_chunks(self):
        """Test embedding multiple chunks."""
        embedder = Embedder()
        texts = [
            "This is the first chunk",
            "This is the second chunk",
        ]

        embeddings = embedder.embed_chunks(texts)

        assert len(embeddings) == 2
        assert all(len(e) == 768 for e in embeddings)

    @pytest.mark.integration
    def test_embed_query(self):
        """Test embedding a single query."""
        embedder = Embedder()
        query = "What is machine learning?"

        embedding = embedder.embed_query(query)

        assert len(embedding) == 768

    def test_embed_chunks_empty(self):
        """Test error on empty texts."""
        embedder = Embedder()

        with pytest.raises(ValueError):
            embedder.embed_chunks([])

    def test_embed_query_empty(self):
        """Test error on empty query."""
        embedder = Embedder()

        with pytest.raises(ValueError):
            embedder.embed_query("")

    def test_get_dimension(self):
        """Test getting embedding dimension."""
        embedder = Embedder()
        assert embedder.get_dimension() == 768


class TestIngestPipeline:
    """Test main ingestion pipeline."""

    @pytest.mark.integration
    def test_ingest_txt_document(self):
        """Test ingesting a text document."""
        content = "This is test document content.\n\nWith multiple sections."

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(content)
            tmp.flush()

            try:
                pipeline = IngestPipeline()
                metadata = {
                    "department": "engineering",
                    "category": "test",
                    "version": "1.0",
                }

                result = pipeline.ingest_document(
                    file_path=tmp.name,
                    metadata=metadata,
                    chunking_strategy="fixed",
                )

                assert result["status"] == "success"
                assert "doc_id" in result
                assert result["chunks_created"] > 0
                assert result["chunking_strategy"] == "fixed"
            finally:
                try:
                    Path(tmp.name).unlink()
                except (PermissionError, OSError):
                    pass

    @pytest.mark.integration
    def test_ingest_with_advanced_strategy(self):
        """Test ingesting with advanced chunking strategy."""
        content = "Section 1\n\nContent here.\n\nSection 2\n\nMore content."

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(content)
            tmp.flush()

            try:
                pipeline = IngestPipeline()
                metadata = {
                    "department": "engineering",
                    "category": "test",
                    "version": "1.0",
                }

                result = pipeline.ingest_document(
                    file_path=tmp.name,
                    metadata=metadata,
                    chunking_strategy="advanced",
                )

                assert result["status"] == "success"
                assert result["chunking_strategy"] == "advanced"
            finally:
                try:
                    Path(tmp.name).unlink()
                except (PermissionError, OSError):
                    pass

    def test_ingest_unsupported_file_type(self):
        """Test error on unsupported file type."""
        with tempfile.NamedTemporaryFile(suffix=".xyz") as tmp:
            pipeline = IngestPipeline()
            metadata = {
                "department": "engineering",
                "category": "test",
                "version": "1.0",
            }

            result = pipeline.ingest_document(
                file_path=tmp.name,
                metadata=metadata,
            )

            assert result["status"] == "error"

    def test_ingest_invalid_metadata(self):
        """Test error on invalid metadata."""
        content = "Test content"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(content)
            tmp.flush()

            try:
                pipeline = IngestPipeline()
                metadata = {
                    "department": "engineering",
                }

                result = pipeline.ingest_document(
                    file_path=tmp.name,
                    metadata=metadata,
                )

                assert result["status"] == "error"
            finally:
                try:
                    Path(tmp.name).unlink()
                except (PermissionError, OSError):
                    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
