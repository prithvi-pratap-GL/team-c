import json
import os
import tempfile
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.middleware.rbac import allowed_departments, get_current_user, require_admin
from app.models import db_models
from app.models.db_models import get_db
from app.models.schemas import (
    Category,
    Department,
    DocumentSummary,
    DocumentsResponse,
    IngestMetadata,
    IngestResponse,
    TokenUser,
)
from app.services.document_service import list_documents
from rag.ingestion.ingest_pipeline import IngestPipeline


router = APIRouter(tags=["documents"])


@router.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_document(
    file: UploadFile = File(...),
    metadata: str = Form(...),
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(require_admin),
):
    try:
        parsed_metadata = IngestMetadata.parse_obj(json.loads(metadata))
    except Exception as exc:
        raise HTTPException(status_code=400, detail="metadata must be valid JSON") from exc

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    suffix = os.path.splitext(file.filename or "")[1] or ".txt"
    temp_path = ""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name

        pipeline_metadata = {
            "department": parsed_metadata.department.value,
            "category": parsed_metadata.category.value,
            "version": parsed_metadata.version,
            "date": parsed_metadata.doc_date.isoformat(),
        }
        chunking_strategy = (
            "fixed" if parsed_metadata.chunking_strategy.value == "fixed" else "advanced"
        )

        pipeline = IngestPipeline()
        pipeline.qdrant_manager.create_collection()
        result = pipeline.ingest_document(
            file_path=temp_path,
            metadata=pipeline_metadata,
            chunking_strategy=chunking_strategy,
        )
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

    if result.get("status") != "success":
        raise HTTPException(status_code=500, detail=result.get("error", "Ingestion failed"))

    document = db_models.Document(
        doc_id=result["doc_id"],
        doc_name=file.filename or "uploaded-document",
        department=parsed_metadata.department.value,
        category=parsed_metadata.category.value,
        version=parsed_metadata.version,
        doc_date=parsed_metadata.doc_date,
        chunking_strategy=chunking_strategy,
        file_type=suffix.lstrip(".").lower(),
        file_size=len(content),
        chunk_count=result.get("chunks_created", 0),
        uploaded_by=current_user.username,
    )
    db.add(document)
    db.commit()

    return IngestResponse(job_id=str(uuid.uuid4()), doc_id=document.doc_id)


@router.get("/documents", response_model=DocumentsResponse)
def get_documents(
    department: Department | None = Query(None),
    category: Category | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(get_current_user),
):
    departments = allowed_departments(current_user, department)
    docs, total = list_documents(
        db,
        departments=departments,
        category=category.value if category else None,
        page=page,
        page_size=page_size,
    )
    return DocumentsResponse(
        documents=[
            DocumentSummary(
                doc_id=doc.doc_id,
                doc_name=doc.doc_name,
                department=doc.department,
                category=doc.category,
                version=doc.version,
                doc_date=doc.doc_date,
                chunk_count=doc.chunk_count,
            )
            for doc in docs
        ],
        total=total,
        page=page,
    )
