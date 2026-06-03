"""Main document ingestion pipeline."""

import logging
from pathlib import Path
from typing import Any, Dict, Literal

from qdrant_client.models import PointStruct

from .chunkers import AdvancedChunker, FixedChunker
from .embedder import Embedder
from .metadata_processor import MetadataProcessor
from .parsers import PDFParser, TxtParser
from .qdrant_client_manager import QdrantClientManager

logger = logging.getLogger(__name__)


class IngestPipeline:
    """Main orchestration for document ingestion."""

    def __init__(self) -> None:
        """Initialize pipeline components."""
        self.qdrant_manager = QdrantClientManager()
        self.embedder = Embedder()
        self.fixed_chunker = FixedChunker()
        self.advanced_chunker = AdvancedChunker()
        self.metadata_processor = MetadataProcessor()

        logger.info("IngestPipeline initialized")

    def ingest_document(
        self,
        file_path: str,
        metadata: Dict[str, Any],
        chunking_strategy: Literal["fixed", "advanced"] = "fixed",
    ) -> Dict[str, Any]:
        """Ingest a single document with specified chunking strategy.

        Pipeline flow:
        1. Detect file type
        2. Parse document
        3. Process metadata
        4. Chunk text
        5. Embed chunks
        6. Upsert to Qdrant

        Args:
            file_path: Path to document.
            metadata: User-provided metadata (department, category, version, date).
            chunking_strategy: 'fixed' or 'advanced'. Defaults to 'fixed'.

        Returns:
            Dictionary with:
            - doc_id: Generated document ID
            - chunks_created: Number of chunks created
            - chunking_strategy: Strategy used
            - status: 'success' or 'error'
            - error: Error message if failed

        Raises:
            ValueError: If file type unsupported or metadata invalid.
        """
        logger.info(
            f"Starting ingestion: {file_path}, strategy={chunking_strategy}"
        )

        try:
            # Step 1: Detect file type and parse
            path = Path(file_path)
            file_ext = path.suffix.lower()

            if file_ext == ".pdf":
                parsed = PDFParser.parse(file_path)
            elif file_ext == ".txt":
                parsed = TxtParser.parse(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")

            logger.info(f"Document parsed: {parsed['document_type']}")

            # Step 2: Process metadata
            processed_metadata = self.metadata_processor.validate_and_process(metadata)
            doc_id = processed_metadata["doc_id"]

            logger.info(f"Metadata processed. doc_id={doc_id}")

            # Step 3: Select chunking strategy
            if chunking_strategy == "fixed":
                chunks = self.fixed_chunker.chunk(parsed["text"])
            elif chunking_strategy == "advanced":
                chunks = self.advanced_chunker.chunk(parsed["text"])
            else:
                raise ValueError(f"Unknown chunking strategy: {chunking_strategy}")

            logger.info(f"Text chunked: {len(chunks)} chunks")

            # Step 4: Embed chunks
            chunk_texts = [chunk["chunk_text"] for chunk in chunks]
            embeddings = self.embedder.embed_chunks(chunk_texts)

            logger.info(f"Chunks embedded: {len(embeddings)} embeddings")

            # Step 5: Upsert to Qdrant
            self._upsert_to_qdrant(
                doc_id=doc_id,
                chunks=chunks,
                embeddings=embeddings,
                metadata=processed_metadata,
                parsed_metadata=parsed.get("metadata", {}),
                chunking_strategy=chunking_strategy,
            )

            logger.info(
                f"Document successfully ingested. "
                f"doc_id={doc_id}, chunks={len(chunks)}"
            )

            return {
                "doc_id": doc_id,
                "chunks_created": len(chunks),
                "chunking_strategy": chunking_strategy,
                "status": "success",
            }

        except Exception as e:
            logger.error(f"Ingestion failed: {e}")
            return {
                "status": "error",
                "error": str(e),
            }

    def _upsert_to_qdrant(
        self,
        doc_id: str,
        chunks: list,
        embeddings: list,
        metadata: Dict[str, Any],
        parsed_metadata: Dict[str, Any],
        chunking_strategy: str,
    ) -> None:
        """Upsert chunks and vectors to Qdrant.

        Payload includes all required fields per specification:
        chunk_id, doc_id, doc_name, department, category, version,
        doc_date, document_type, chunk_text, chunking_strategy

        Args:
            doc_id: Document ID.
            chunks: List of chunks with chunk_id and chunk_text.
            embeddings: List of embedding vectors.
            metadata: Processed metadata.
            parsed_metadata: Parsed document metadata.
            chunking_strategy: Strategy used for chunking.
        """
        client = self.qdrant_manager.get_client()

        points = []
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            payload = {
                "chunk_id": chunk["chunk_id"],
                "doc_id": doc_id,
                "doc_name": parsed_metadata.get("filename", "unknown"),
                "department": metadata.get("department", ""),
                "category": metadata.get("category", ""),
                "version": metadata.get("version", ""),
                "doc_date": metadata.get("date"),
                "document_type": parsed_metadata.get("document_type", ""),
                "chunk_text": chunk["chunk_text"],
                "chunking_strategy": chunking_strategy,
            }

            point = PointStruct(
                id=hash(f"{doc_id}_{chunk['chunk_id']}") & 0x7FFFFFFF,
                vector=embedding,
                payload=payload,
            )
            points.append(point)

        self.qdrant_manager.get_client().upsert(
            collection_name=self.qdrant_manager.COLLECTION_NAME,
            points=points,
        )

        logger.info(
            f"Upserted {len(points)} points to Qdrant "
            f"(collection={self.qdrant_manager.COLLECTION_NAME})"
        )
