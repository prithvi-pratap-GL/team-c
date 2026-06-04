import json
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.middleware.rbac import allowed_departments, get_current_user, require_admin
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
from app.services.document_service import create_document, list_documents


router = APIRouter(tags=["documents"])


@router.options("/ingest")
async def options_ingest():
    return {}


@router.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_document(
    file: UploadFile = File(...),
    metadata: str = Form(...),
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(require_admin),
):
    try:
        parsed_metadata = IngestMetadata.parse_obj(json.loads(metadata))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"metadata is not valid JSON: {str(exc)}")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid metadata: {str(exc)}")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    document = create_document(db, file, content, parsed_metadata, current_user)
    return IngestResponse(job_id=str(uuid.uuid4()), doc_id=document.doc_id)


@router.options("/documents")
def options_documents():
    return {}


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
                doc_date=doc.doc_date.isoformat() if doc.doc_date else "",
                chunk_count=doc.chunk_count,
            )
            for doc in docs
        ],
        total=total,
        page=page,
    )
