import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.middleware.rbac import allowed_departments, get_current_user
from app.models import db_models
from app.models.db_models import get_db
from app.models.schemas import ChatRequest, ChatResponse, Confidence, Source, TokenUser
from rag.generation.groq_client import GroqClientService
from rag.generation.prompt_builder import PromptBuilder
from rag.retrieval.hybrid_retriever import HybridRetriever
from rag.retrieval.metadata_filter import MetadataFilterBuilder


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
    qdrant_filter = MetadataFilterBuilder.combined_filter(
        departments=[department.value for department in departments],
        categories=[payload.filters.category.value] if payload.filters.category else None,
    )

    try:
        results = HybridRetriever().retrieve(
            payload.query,
            top_k=10,
            rerank=True,
            rerank_top_k=settings.max_sources,
            query_filter=qdrant_filter,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Retrieval failed: {exc}") from exc

    top_score = float(results[0].get("score", 0)) if results else 0
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
                doc_id=str(result.get("metadata", {}).get("doc_id", "")),
                doc_name=str(result.get("metadata", {}).get("doc_name", "Unknown Document")),
                department=result.get("metadata", {}).get("department") or departments[0].value,
                chunk_text=str(result.get("chunk_text", ""))[:200],
                chunk_id=str(result.get("metadata", {}).get("chunk_id", "")),
                score=float(result.get("score", 0)),
                page=None,
            )
            for result in results
        ]

        try:
            system_prompt, user_prompt = PromptBuilder.build_prompt(payload.query, results)
            answer = GroqClientService().generate(system_prompt, user_prompt)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Generation failed: {exc}") from exc

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
