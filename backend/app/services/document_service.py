import os
import uuid
import threading
import logging
from typing import List, Optional

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models import db_models
from app.models.schemas import Department, IngestMetadata, TokenUser
from app.rag.ingestion.ingest_pipeline import IngestPipeline

logger = logging.getLogger(__name__)


def _ingest_document_background(
    doc_id: str,
    temp_path: str,
    file_name: str,
    metadata_dict: dict,
    chunking_strategy: str,
) -> None:
    """Background task for document ingestion (runs in separate thread)."""
    try:
        pipeline = IngestPipeline()
        result = pipeline.ingest_document(
            file_path=temp_path,
            metadata=metadata_dict,
            chunking_strategy=chunking_strategy,
        )
        logger.info(
            f"Background ingestion completed: doc_id={doc_id}, "
            f"chunks={result['chunks_created']}"
        )
    except Exception as e:
        logger.error(f"Background ingestion failed for doc_id={doc_id}: {e}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def create_document(
    db: Session,
    file: UploadFile,
    content: bytes,
    metadata: IngestMetadata,
    current_user: TokenUser,
) -> db_models.Document:
    """
    Create document metadata and start async ingestion.

    Flow:
    1. Save temp file
    2. Create DB record (chunk_count=0 initially)
    3. Start background thread for embedding
    4. Return 202 ACCEPTED immediately
    5. Background thread processes embedding → Qdrant
    """

    doc_id = str(uuid.uuid4())
    temp_path = f"temp_{uuid.uuid4()}_{file.filename}"

    try:
        # Save uploaded file temporarily
        with open(temp_path, "wb") as f:
            f.write(content)

        # Create document record with placeholder chunk_count
        document = db_models.Document(
            doc_id=doc_id,
            doc_name=file.filename or "uploaded-document",
            department=metadata.department.value,
            category=metadata.category.value,
            version=metadata.version,
            doc_date=metadata.doc_date,
            chunking_strategy=metadata.chunking_strategy.value,
            file_type=(file.filename or "").split(".")[-1].lower()
            or "unknown",
            file_size=len(content),
            chunk_count=0,  # Will be updated by background task
            uploaded_by=current_user.username,
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        # Start background ingestion thread (non-blocking)
        thread = threading.Thread(
            target=_ingest_document_background,
            args=(
                doc_id,
                temp_path,
                file.filename,
                {
                    "department": metadata.department.value,
                    "category": metadata.category.value,
                    "version": metadata.version,
                    "date": str(metadata.doc_date),
                },
                metadata.chunking_strategy.value,
            ),
            daemon=True,
        )
        thread.start()
        logger.info(f"Started background ingestion thread for doc_id={doc_id}")

        return document

    except Exception as e:
        logger.error(f"Failed to create document: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise


def list_documents(
    db: Session,
    departments: List[Department],
    category: Optional[str],
    page: int,
    page_size: int,
) -> tuple[List[db_models.Document], int]:
    """
    List uploaded document metadata.

    SQLite remains source of truth for metadata.
    """

    query = db.query(db_models.Document).filter(
        db_models.Document.department.in_(
            [dept.value for dept in departments]
        )
    )

    if category:
        query = query.filter(
            db_models.Document.category == category
        )

    total = query.count()

    documents = (
        query.order_by(db_models.Document.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return documents, total


# Temporary compatibility shim
# Will be removed after chat.py migrates to HybridRetriever
def search_chunks(*args, **kwargs):
    raise NotImplementedError(
        "Local chunk search removed. Use HybridRetriever in chat router."
    )