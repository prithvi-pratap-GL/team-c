import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import get_settings
from app.middleware.rbac import allowed_departments, get_current_user
from app.models import db_models
from app.models.db_models import get_db
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    Confidence,
    Source,
    TokenUser,
)

from app.rag.retrieval.hybrid_retriever import HybridRetriever
from app.rag.generation.prompt_builder import PromptBuilder
from app.rag.generation.groq_client import GroqClientService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.options("")
def options_chat():
    return {}


@router.post("", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(get_current_user),
):
    settings = get_settings()

    session_id = payload.session_id or str(uuid.uuid4())

    # RBAC department resolution
    departments = allowed_departments(
        current_user,
        payload.filters.department,
    )

    retriever = HybridRetriever()

    # TODO:
    # Wire MetadataFilterBuilder later using departments
    results = retriever.retrieve(
        query=payload.query,
        top_k=settings.max_sources,
    )

    top_score = results[0]["score"] if results else 0

    if not results:
        response = ChatResponse(
            answer="I could not find relevant information in the knowledge base.",
            sources=[],
            retrieval_mode_used=payload.retrieval_mode,
            confidence=Confidence.not_found,
            session_id=session_id,
        )

    else:
        # Build prompts
        builder = PromptBuilder()

        system_prompt, user_prompt = builder.build_prompt(
            query=payload.query,
            retrieval_results=results,
        )

        # Generate answer using Groq
        groq = GroqClientService()

        answer = groq.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        # Build sources
        sources = [
            Source(
                doc_id=r["metadata"].get("doc_id", ""),
                doc_name=r["metadata"].get(
                    "doc_name",
                    "Unknown Document",
                ),
                department=r["metadata"].get("department"),
                chunk_text=r["chunk_text"][:200],
                chunk_id=r["metadata"].get("chunk_id", ""),
                score=r["score"],
                page=None,
            )
            for r in results
        ]

        response = ChatResponse(
            answer=answer,
            sources=sources,
            retrieval_mode_used=payload.retrieval_mode,
            confidence=(
                Confidence.high
                if top_score >= 0.5
                else Confidence.low
            ),
            session_id=session_id,
        )

    # Persist chat log
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