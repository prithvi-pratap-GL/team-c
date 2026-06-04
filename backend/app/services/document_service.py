import os
import uuid
from typing import List, Optional

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models import db_models
from app.models.schemas import Department, IngestMetadata, TokenUser
from app.rag.ingestion.ingest_pipeline import IngestPipeline


def create_document(
    db: Session,
    file: UploadFile,
    content: bytes,
    metadata: IngestMetadata,
    current_user: TokenUser,
) -> db_models.Document:
    """
    Create document metadata and ingest via P3 pipeline.

    Flow:
    upload
    → temp file
    → P3 IngestPipeline
    → embeddings
    → Qdrant
    → SQLite metadata
    """

    doc_id = str(uuid.uuid4())

    temp_path = f"temp_{uuid.uuid4()}_{file.filename}"

    try:
        # Save uploaded file temporarily
        with open(temp_path, "wb") as f:
            f.write(content)

        # P3 ingestion pipeline
        pipeline = IngestPipeline()

        result = pipeline.ingest_document(
            file_path=temp_path,
            metadata={
                "department": metadata.department.value,
                "category": metadata.category.value,
                "version": metadata.version,
                "date": str(metadata.doc_date),
            },
            chunking_strategy=metadata.chunking_strategy.value,
        )

        # SQLite metadata only
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
            chunk_count=result["chunks_created"],
            uploaded_by=current_user.username,
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        return document

    finally:
        # cleanup temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)


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