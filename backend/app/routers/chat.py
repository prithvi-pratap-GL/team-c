import json
import logging
import re
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.middleware.rbac import allowed_departments, get_current_user
from app.models import db_models
from app.models.db_models import get_db
from app.models.schemas import (
    ChatFilters,
    ChatMessageResponse,
    ChatRequest,
    ChatResponse,
    ChatSessionCreate,
    ChatSessionResponse,
    Confidence,
    RetrievalMode,
    SessionChatRequest,
    Source,
    SuggestionsResponse,
    TokenUser,
)
from app.rag.generation.groq_client import GroqClientService
from app.rag.generation.prompt_builder import PromptBuilder, sanitize_llm_response
from app.rag.retrieval.hybrid_retriever import HybridRetriever
from app.rag.retrieval.metadata_filter import MetadataFilterBuilder

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


# ─────────────────────────────────────────────────────────────────────
# Helper: get user DB record (needed for FK)
# ─────────────────────────────────────────────────────────────────────

def _get_user_record(db: Session, token_user: TokenUser) -> db_models.User:
    user = db.query(db_models.User).filter(db_models.User.username == token_user.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User record not found")
    return user


# ─────────────────────────────────────────────────────────────────────
# Helper: auto-generate a session title from the first user message
# ─────────────────────────────────────────────────────────────────────

def _generate_title(query: str) -> str:
    """
    Strip question marks / filler, title-case first 50 chars.
    No AI, no hardcoded strings.
    """
    # Remove leading question words only if followed by more content
    cleaned = re.sub(
        r"^(what is|what are|how does|how do|explain|describe|tell me about|can you explain)\s+",
        "",
        query.strip(),
        flags=re.IGNORECASE,
    )
    cleaned = cleaned.rstrip("?!.").strip()
    if not cleaned:
        cleaned = query.strip().rstrip("?!.")
    # Title-case and truncate
    title = cleaned[:50]
    if len(query.strip()) > 50:
        # find last space before 50 to avoid mid-word cut
        last_space = title.rfind(" ")
        if last_space > 20:
            title = title[:last_space]
    return title.title() or "New Conversation"


# ─────────────────────────────────────────────────────────────────────
# RAG execution (shared by legacy /chat and new session endpoint)
# ─────────────────────────────────────────────────────────────────────

def _run_rag(
    query: str,
    filters: ChatFilters,
    retrieval_mode: RetrievalMode,
    session_id: str,
    current_user: TokenUser,
    db: Session,
) -> ChatResponse:
    settings = get_settings()

    departments = allowed_departments(current_user, filters.department)
    query_filter = MetadataFilterBuilder.combined_filter(
        departments=departments,
        categories=[filters.category] if filters.category else None,
    )

    retriever = HybridRetriever()
    results = retriever.retrieve(query=query, top_k=settings.max_sources, query_filter=query_filter)

    qdrant_score = results[0].get("score", 0) if results else 0

    if results and qdrant_score < settings.min_retrieval_score:
        results = []
        qdrant_score = 0

    if not results:
        response = ChatResponse(
            answer="I could not find relevant information in the knowledge base.",
            sources=[],
            retrieval_mode_used=retrieval_mode,
            confidence=Confidence.not_found,
            session_id=session_id,
        )
    else:
        builder = PromptBuilder()
        system_prompt, user_prompt = builder.build_prompt(query=query, retrieval_results=results)
        groq = GroqClientService()
        answer = sanitize_llm_response(groq.generate(system_prompt=system_prompt, user_prompt=user_prompt))

        sources = [
            Source(
                doc_id=r["metadata"].get("doc_id", ""),
                doc_name=r["metadata"].get("doc_name", "Unknown Document"),
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
            retrieval_mode_used=retrieval_mode,
            confidence=Confidence.high if qdrant_score >= 0.5 else Confidence.low,
            session_id=session_id,
        )

    # Persist legacy chat log
    db.add(
        db_models.ChatLog(
            session_id=session_id,
            username=current_user.username,
            query=query,
            answer=response.answer,
            confidence=response.confidence.value,
            top_score=qdrant_score,
        )
    )
    return response


# ─────────────────────────────────────────────────────────────────────
# Legacy endpoint (kept for backward compatibility)
# ─────────────────────────────────────────────────────────────────────

@router.post("", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(get_current_user),
):
    session_id = payload.session_id or str(uuid.uuid4())
    response = _run_rag(
        query=payload.query,
        filters=payload.filters,
        retrieval_mode=payload.retrieval_mode,
        session_id=session_id,
        current_user=current_user,
        db=db,
    )
    db.commit()
    return response


# ─────────────────────────────────────────────────────────────────────
# SESSION CRUD
# ─────────────────────────────────────────────────────────────────────

@router.post("/sessions", response_model=ChatSessionResponse, status_code=201)
def create_session(
    payload: ChatSessionCreate,
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(get_current_user),
):
    user = _get_user_record(db, current_user)
    now = datetime.utcnow()
    session = db_models.ChatSession(
        user_id=user.id,
        title=payload.title or "New Conversation",
        created_at=now,
        updated_at=now,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/sessions", response_model=List[ChatSessionResponse])
def list_sessions(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(get_current_user),
):
    user = _get_user_record(db, current_user)
    sessions = (
        db.query(db_models.ChatSession)
        .filter(db_models.ChatSession.user_id == user.id)
        .order_by(db_models.ChatSession.updated_at.desc())
        .limit(limit)
        .all()
    )
    return sessions


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(get_current_user),
):
    user = _get_user_record(db, current_user)
    session = (
        db.query(db_models.ChatSession)
        .filter(
            db_models.ChatSession.id == session_id,
            db_models.ChatSession.user_id == user.id,
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(get_current_user),
):
    user = _get_user_record(db, current_user)
    session = (
        db.query(db_models.ChatSession)
        .filter(
            db_models.ChatSession.id == session_id,
            db_models.ChatSession.user_id == user.id,
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(session)
    db.commit()


# ─────────────────────────────────────────────────────────────────────
# MESSAGES
# ─────────────────────────────────────────────────────────────────────

@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
def get_messages(
    session_id: int,
    limit: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(get_current_user),
):
    user = _get_user_record(db, current_user)
    session = (
        db.query(db_models.ChatSession)
        .filter(
            db_models.ChatSession.id == session_id,
            db_models.ChatSession.user_id == user.id,
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = (
        db.query(db_models.ChatMessage)
        .filter(db_models.ChatMessage.session_id == session_id)
        .order_by(db_models.ChatMessage.created_at)
        .limit(limit)
        .all()
    )
    return messages


@router.post("/sessions/{session_id}/messages", response_model=ChatResponse)
def send_message(
    session_id: int,
    payload: SessionChatRequest,
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(get_current_user),
):
    user = _get_user_record(db, current_user)
    session = (
        db.query(db_models.ChatSession)
        .filter(
            db_models.ChatSession.id == session_id,
            db_models.ChatSession.user_id == user.id,
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Save user message
    user_msg = db_models.ChatMessage(
        session_id=session_id,
        role="user",
        content=payload.query,
    )
    db.add(user_msg)

    # Auto-title on first message
    is_first = (
        db.query(db_models.ChatMessage)
        .filter(db_models.ChatMessage.session_id == session_id)
        .count()
        == 0  # count BEFORE adding the one above (not yet flushed)
    )
    if is_first and session.title == "New Conversation":
        session.title = _generate_title(payload.query)

    # Run RAG
    response = _run_rag(
        query=payload.query,
        filters=payload.filters,
        retrieval_mode=payload.retrieval_mode,
        session_id=str(session_id),
        current_user=current_user,
        db=db,
    )

    # Save assistant message with serialized metadata
    meta = {
        "confidence": response.confidence.value,
        "retrieval_mode_used": response.retrieval_mode_used.value,
        "sources": [s.model_dump() for s in response.sources],
    }
    assistant_msg = db_models.ChatMessage(
        session_id=session_id,
        role="assistant",
        content=response.answer,
        meta_json=json.dumps(meta),
    )
    db.add(assistant_msg)

    # Touch updated_at
    session.updated_at = datetime.utcnow()

    db.commit()

    # Return response with integer session_id as string for consistency
    response.session_id = str(session_id)
    return response


# ─────────────────────────────────────────────────────────────────────
# SUGGESTIONS
# ─────────────────────────────────────────────────────────────────────

_QUESTION_TEMPLATES = [
    "What is the {topic}?",
    "How does {topic} work?",
    "Explain {topic}",
    "What are the guidelines for {topic}?",
    "What is the process for {topic}?",
]


def _doc_to_suggestion(doc_name: str, category: str) -> str:
    """
    Derive a natural question from a document name + category.
    No hardcoded strings — driven entirely by document metadata.
    """
    # Strip file extensions and version tokens
    name = re.sub(r"\.(pdf|txt|docx|md)$", "", doc_name, flags=re.IGNORECASE)
    name = re.sub(r"[_\-]v?\d+(\.\d+)*$", "", name).strip()
    name = re.sub(r"[_\-]", " ", name).strip()

    if not name:
        return ""

    name_lower = name.lower()
    cat = (category or "").lower()

    if cat in ("policy", "guide", "faq"):
        return f"What is the {name_lower}?"
    elif cat == "incident":
        return f"What is the process for {name_lower}?"
    elif cat == "release_notes":
        return f"What changed in {name_lower}?"
    else:
        return f"Explain {name_lower}"


@router.get("/suggestions", response_model=SuggestionsResponse)
def get_suggestions(
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(get_current_user),
):
    """
    Return dynamic suggested questions derived from documents the user
    can access.  No hardcoded strings — all generated from document
    metadata.
    """
    dept_values = [d.value for d in current_user.departments_allowed]

    docs = (
        db.query(db_models.Document)
        .filter(db_models.Document.department.in_(dept_values))
        .order_by(db_models.Document.created_at.desc())
        .limit(20)
        .all()
    )

    seen: set = set()
    suggestions: List[str] = []

    for doc in docs:
        suggestion = _doc_to_suggestion(doc.doc_name, doc.category)
        if suggestion and suggestion not in seen:
            seen.add(suggestion)
            suggestions.append(suggestion)
        if len(suggestions) >= 6:
            break

    return SuggestionsResponse(suggestions=suggestions)
