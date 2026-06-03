import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import get_settings
from app.middleware.rbac import allowed_departments, get_current_user
from app.models import db_models
from app.models.db_models import get_db
from app.models.schemas import ChatRequest, ChatResponse, Confidence, Source, TokenUser
from app.services.document_service import search_chunks


router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(get_current_user),
):
    settings = get_settings()
    session_id = payload.session_id or str(uuid.uuid4())
    departments = allowed_departments(current_user, payload.filters.department)

    results = search_chunks(
        db,
        query_text=payload.query,
        departments=departments,
        category=payload.filters.category.value if payload.filters.category else None,
        year=payload.filters.year,
        limit=settings.max_sources,
    )

    top_score = results[0][1] if results else 0
    if top_score < settings.min_retrieval_score:
        answer = "I cannot find this in the knowledge base for your access level."
        response = ChatResponse(
            answer=answer,
            sources=[],
            retrieval_mode_used=payload.retrieval_mode,
            confidence=Confidence.not_found,
            session_id=session_id,
        )
    else:
        sources = [
            Source(
                doc_id=chunk.document.doc_id,
                doc_name=chunk.document.doc_name,
                department=chunk.document.department,
                chunk_text=chunk.chunk_text[:200],
                chunk_id=chunk.chunk_id,
                score=score,
                page=chunk.page,
            )
            for chunk, score in results
        ]
        answer = (
            f"Based on the available knowledge base, the most relevant source says: "
            f"{results[0][0].chunk_text[:700]}"
        )
        response = ChatResponse(
            answer=answer,
            sources=sources,
            retrieval_mode_used=payload.retrieval_mode,
            confidence=Confidence.high if top_score >= 0.4 else Confidence.low,
            session_id=session_id,
        )

    db.add(
        db_models.ChatLog(
            session_id=session_id,
            username=current_user.username,
            query=payload.query,
            answer=response.answer,
            confidence=response.confidence.value,
            top_score=top_score,
        )
    )
    db.commit()
    return response
