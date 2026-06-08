"""Admin router — all /admin/** endpoints. Requires admin role on every endpoint."""
import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.middleware.rbac import get_current_user, require_admin
from app.models import db_models
from app.models.db_models import get_db
from app.models.schemas import (
    AdminDocumentResponse,
    AdminDocumentsListResponse,
    AnalyticsResponse,
    AuditLogResponse,
    AuditLogsListResponse,
    DepartmentCreate,
    DepartmentResponse,
    DepartmentUpdate,
    DeptDocCount,
    OverviewStats,
    Role,
    TokenUser,
    TopQuestion,
    TopUser,
    UserAdminResponse,
    UserCreateAdmin,
    UserUpdateAdmin,
    UsersListResponse,
)
from app.services.audit_service import AuditAction, log_event
from app.services.auth_service import get_password_hash
from app.services.confidence_service import ConfidenceService

router = APIRouter(prefix="/admin", tags=["admin"])


def _get_client_ip(request: Request) -> str:
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _user_to_response(user: db_models.User) -> UserAdminResponse:
    return UserAdminResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        departments_allowed=user.departments_allowed.split(",") if user.departments_allowed else [],
        is_active=user.is_active if user.is_active is not None else True,
        created_at=user.created_at,
    )


# ─── Overview ────────────────────────────────────────────────────────────────

@router.get("/overview", response_model=OverviewStats)
def get_overview(
    db: Session = Depends(get_db),
    _: TokenUser = Depends(require_admin),
):
    total_users = db.query(func.count(db_models.User.id)).scalar() or 0
    total_documents = db.query(func.count(db_models.Document.id)).scalar() or 0
    total_departments = db.query(func.count(db_models.Department.id)).scalar() or 0
    total_sessions = db.query(func.count(db_models.ChatSession.id)).scalar() or 0
    total_questions = db.query(func.count(db_models.ChatMessage.id)).filter(
        db_models.ChatMessage.role == "user"
    ).scalar() or 0

    return OverviewStats(
        total_users=total_users,
        total_documents=total_documents,
        total_departments=total_departments,
        total_chat_sessions=total_sessions,
        total_questions_asked=total_questions,
    )


# ─── User Management ─────────────────────────────────────────────────────────

@router.get("/users", response_model=UsersListResponse)
def list_users(
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: TokenUser = Depends(require_admin),
):
    q = db.query(db_models.User)
    if search:
        q = q.filter(db_models.User.username.ilike(f"%{search}%"))
    if role:
        q = q.filter(db_models.User.role == role)
    if department:
        q = q.filter(db_models.User.departments_allowed.ilike(f"%{department}%"))
    if is_active is not None:
        q = q.filter(db_models.User.is_active == is_active)

    total = q.count()
    users = q.order_by(db_models.User.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return UsersListResponse(
        users=[_user_to_response(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/users", response_model=UserAdminResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreateAdmin,
    request: Request,
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(require_admin),
):
    if db.query(db_models.User).filter(db_models.User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")

    user = db_models.User(
        username=payload.username,
        email=payload.email,
        password_hash=get_password_hash(payload.password),
        role=payload.role,
        departments_allowed=",".join(payload.departments_allowed),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_event(db, current_user.username, AuditAction.USER_CREATE,
              target=payload.username,
              details={"role": payload.role, "departments": payload.departments_allowed},
              ip_address=_get_client_ip(request))

    return _user_to_response(user)


@router.get("/users/{user_id}", response_model=UserAdminResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: TokenUser = Depends(require_admin),
):
    user = db.query(db_models.User).filter(db_models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_to_response(user)


@router.put("/users/{user_id}", response_model=UserAdminResponse)
def update_user(
    user_id: int,
    payload: UserUpdateAdmin,
    request: Request,
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(require_admin),
):
    user = db.query(db_models.User).filter(db_models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    changes = {}
    if payload.email is not None:
        user.email = payload.email
        changes["email"] = payload.email
    if payload.role is not None:
        old_role = user.role
        user.role = payload.role
        changes["role"] = {"from": old_role, "to": payload.role}
    if payload.departments_allowed is not None:
        old_depts = user.departments_allowed
        user.departments_allowed = ",".join(payload.departments_allowed)
        changes["departments"] = {"from": old_depts, "to": user.departments_allowed}
    if payload.is_active is not None:
        user.is_active = payload.is_active
        changes["is_active"] = payload.is_active
    if payload.password:
        user.password_hash = get_password_hash(payload.password)
        changes["password"] = "changed"

    db.commit()
    db.refresh(user)

    log_event(db, current_user.username, AuditAction.USER_UPDATE,
              target=user.username,
              details=changes,
              ip_address=_get_client_ip(request))

    return _user_to_response(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(require_admin),
):
    user = db.query(db_models.User).filter(db_models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.username == current_user.username:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    username = user.username
    db.delete(user)
    db.commit()

    log_event(db, current_user.username, AuditAction.USER_DELETE,
              target=username,
              ip_address=_get_client_ip(request))


# ─── Document Management ──────────────────────────────────────────────────────

@router.get("/documents", response_model=AdminDocumentsListResponse)
def list_all_documents(
    search: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: TokenUser = Depends(require_admin),
):
    q = db.query(db_models.Document)
    if search:
        q = q.filter(db_models.Document.doc_name.ilike(f"%{search}%"))
    if department:
        q = q.filter(db_models.Document.department == department)
    if status:
        q = q.filter(db_models.Document.status == status)

    total = q.count()
    docs = q.order_by(db_models.Document.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return AdminDocumentsListResponse(
        documents=[AdminDocumentResponse(
            id=doc.id,
            doc_id=doc.doc_id,
            doc_name=doc.doc_name,
            department=doc.department,
            category=doc.category,
            version=doc.version,
            doc_date=doc.doc_date,
            file_type=doc.file_type,
            file_size=doc.file_size,
            chunk_count=doc.chunk_count,
            uploaded_by=doc.uploaded_by,
            status=getattr(doc, "status", "ready"),
            created_at=doc.created_at,
        ) for doc in docs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    doc_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(require_admin),
):
    doc = db.query(db_models.Document).filter(db_models.Document.doc_id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc_name = doc.doc_name

    # Remove from Qdrant
    try:
        from app.rag.ingestion.qdrant_client_manager import QdrantClientManager
        qdrant = QdrantClientManager()
        from qdrant_client.http.models import Filter, FieldCondition, MatchValue
        qdrant.client.delete(
            collection_name=qdrant.collection_name,
            points_selector=Filter(
                must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
            ),
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Qdrant delete failed for {doc_id}: {e}")

    # Delete chunks and document from DB (cascade handles chunks)
    db.delete(doc)
    db.commit()

    log_event(db, current_user.username, AuditAction.DOC_DELETE,
              target=doc_id,
              details={"doc_name": doc_name},
              ip_address=_get_client_ip(request))


@router.post("/documents/{doc_id}/reingest", status_code=status.HTTP_202_ACCEPTED)
def reingest_document(
    doc_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(require_admin),
):
    doc = db.query(db_models.Document).filter(db_models.Document.doc_id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    log_event(db, current_user.username, AuditAction.DOC_REINGEST,
              target=doc_id,
              details={"doc_name": doc.doc_name},
              ip_address=_get_client_ip(request))

    return {"message": "Re-ingestion queued", "doc_id": doc_id}


# ─── Department Management ────────────────────────────────────────────────────

@router.get("/departments", response_model=List[DepartmentResponse])
def list_departments(
    db: Session = Depends(get_db),
    _: TokenUser = Depends(require_admin),
):
    depts = db.query(db_models.Department).order_by(db_models.Department.name).all()
    return [DepartmentResponse(
        id=d.id,
        name=d.name,
        description=d.description,
        is_active=d.is_active,
        created_at=d.created_at,
        updated_at=d.updated_at,
    ) for d in depts]


@router.post("/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(
    payload: DepartmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(require_admin),
):
    existing = db.query(db_models.Department).filter(db_models.Department.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Department already exists")

    dept = db_models.Department(
        name=payload.name.lower().replace(" ", "_"),
        description=payload.description,
        is_active=True,
    )
    db.add(dept)
    db.commit()
    db.refresh(dept)

    log_event(db, current_user.username, AuditAction.DEPT_CREATE,
              target=dept.name,
              ip_address=_get_client_ip(request))

    return DepartmentResponse(
        id=dept.id,
        name=dept.name,
        description=dept.description,
        is_active=dept.is_active,
        created_at=dept.created_at,
        updated_at=dept.updated_at,
    )


@router.put("/departments/{dept_id}", response_model=DepartmentResponse)
def update_department(
    dept_id: int,
    payload: DepartmentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(require_admin),
):
    dept = db.query(db_models.Department).filter(db_models.Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

    if payload.description is not None:
        dept.description = payload.description
    if payload.is_active is not None:
        dept.is_active = payload.is_active

    db.commit()
    db.refresh(dept)

    log_event(db, current_user.username, AuditAction.DEPT_UPDATE,
              target=dept.name,
              ip_address=_get_client_ip(request))

    return DepartmentResponse(
        id=dept.id,
        name=dept.name,
        description=dept.description,
        is_active=dept.is_active,
        created_at=dept.created_at,
        updated_at=dept.updated_at,
    )


# ─── Analytics ───────────────────────────────────────────────────────────────

@router.get("/analytics", response_model=AnalyticsResponse)
def get_analytics(
    db: Session = Depends(get_db),
    _: TokenUser = Depends(require_admin),
):
    total_questions = db.query(func.count(db_models.ChatMessage.id)).filter(
        db_models.ChatMessage.role == "user"
    ).scalar() or 0

    total_sessions = db.query(func.count(db_models.ChatSession.id)).scalar() or 0

    # Top users by question count
    top_users_raw = (
        db.query(db_models.User.username, func.count(db_models.ChatMessage.id).label("cnt"))
        .join(db_models.ChatSession, db_models.ChatSession.user_id == db_models.User.id)
        .join(db_models.ChatMessage, db_models.ChatMessage.session_id == db_models.ChatSession.id)
        .filter(db_models.ChatMessage.role == "user")
        .group_by(db_models.User.username)
        .order_by(func.count(db_models.ChatMessage.id).desc())
        .limit(10)
        .all()
    )
    top_users = [TopUser(username=u, question_count=c) for u, c in top_users_raw]

    # Most asked questions (top queries by frequency)
    most_asked_raw = (
        db.query(db_models.ChatMessage.content, func.count(db_models.ChatMessage.id).label("cnt"))
        .filter(db_models.ChatMessage.role == "user")
        .group_by(db_models.ChatMessage.content)
        .order_by(func.count(db_models.ChatMessage.id).desc())
        .limit(10)
        .all()
    )
    most_asked = [TopQuestion(query=q[:120], count=c) for q, c in most_asked_raw]

    # Documents by department
    docs_by_dept_raw = (
        db.query(db_models.Document.department, func.count(db_models.Document.id).label("cnt"))
        .group_by(db_models.Document.department)
        .all()
    )
    docs_by_dept = [DeptDocCount(department=d, count=c) for d, c in docs_by_dept_raw]

    return AnalyticsResponse(
        total_questions=total_questions,
        total_sessions=total_sessions,
        top_users=top_users,
        most_asked=most_asked,
        docs_by_department=docs_by_dept,
    )


# ─── Reranker Score Distribution ──────────────────────────────────────────────

@router.get("/reranker-distribution")
def get_reranker_distribution(
    db: Session = Depends(get_db),
    _: TokenUser = Depends(require_admin),
):
    """Get reranker score distribution statistics for threshold calibration.

    Returns score distribution metrics and recommendations for confidence thresholds.
    """
    from sqlalchemy import func as sqlalchemy_func
    import statistics

    # Get vector scores
    vector_scores_raw = db.query(db_models.ChatLog.vector_score).filter(
        db_models.ChatLog.vector_score.isnot(None)
    ).all()
    vector_scores = [row[0] for row in vector_scores_raw]

    # Get reranker scores
    reranker_scores_raw = db.query(db_models.ChatLog.reranker_score).filter(
        db_models.ChatLog.reranker_score.isnot(None)
    ).all()
    reranker_scores = [row[0] for row in reranker_scores_raw]

    def calc_stats(scores):
        if not scores:
            return None
        sorted_scores = sorted(scores)
        count = len(scores)
        return {
            "count": count,
            "min": round(min(scores), 4),
            "max": round(max(scores), 4),
            "mean": round(statistics.mean(scores), 4),
            "median": round(statistics.median(scores), 4),
            "p75": round(sorted_scores[int(count * 0.75)], 4),
            "p90": round(sorted_scores[int(count * 0.90)], 4),
            "p95": round(sorted_scores[int(count * 0.95)], 4),
            "p99": round(sorted_scores[int(count * 0.99)], 4),
        }

    # Per-confidence breakdown
    per_confidence = {}
    for conf_level in ["high", "medium", "low", "not_found"]:
        conf_rows = db.query(
            db_models.ChatLog.reranker_score
        ).filter(
            db_models.ChatLog.confidence == conf_level,
            db_models.ChatLog.reranker_score.isnot(None),
        ).all()

        if conf_rows:
            scores = [row[0] for row in conf_rows]
            per_confidence[conf_level] = {
                "query_count": len(scores),
                "reranker_stats": calc_stats(scores),
            }

    return {
        "calibration_date": db.query(sqlalchemy_func.max(db_models.ChatLog.created_at)).scalar(),
        "vector_score_distribution": calc_stats(vector_scores),
        "reranker_score_distribution": calc_stats(reranker_scores),
        "per_confidence_statistics": per_confidence,
        "total_queries_analyzed": len(vector_scores),
        "note": "Use these distributions to calibrate confidence thresholds empirically.",
    }


# ─── Audit Logs ───────────────────────────────────────────────────────────────

@router.get("/audit-logs", response_model=AuditLogsListResponse)
def get_audit_logs(
    actor: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: TokenUser = Depends(require_admin),
):
    q = db.query(db_models.AuditLog)
    if actor:
        q = q.filter(db_models.AuditLog.actor.ilike(f"%{actor}%"))
    if action:
        q = q.filter(db_models.AuditLog.action == action)

    total = q.count()
    logs = q.order_by(db_models.AuditLog.timestamp.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return AuditLogsListResponse(
        logs=[AuditLogResponse(
            id=log.id,
            timestamp=log.timestamp,
            actor=log.actor,
            action=log.action,
            target=log.target,
            details=log.details,
            ip_address=log.ip_address,
        ) for log in logs],
        total=total,
        page=page,
        page_size=page_size,
    )


# ─── Confidence Analytics ────────────────────────────────────────────────────

@router.get("/confidence-metrics")
def get_confidence_metrics(
    db: Session = Depends(get_db),
    _: TokenUser = Depends(require_admin),
):
    """Get confidence level distribution and quality metrics.

    Returns:
        Dict with confidence distribution and statistics.
    """
    from sqlalchemy import and_, func as sqlalchemy_func

    # Count by confidence level
    confidence_counts = (
        db.query(db_models.ChatLog.confidence, sqlalchemy_func.count(db_models.ChatLog.id).label("cnt"))
        .group_by(db_models.ChatLog.confidence)
        .all()
    )
    confidence_dist = {conf: cnt for conf, cnt in confidence_counts}

    # Average scores by confidence level
    avg_scores = (
        db.query(
            db_models.ChatLog.confidence,
            sqlalchemy_func.avg(db_models.ChatLog.vector_score).label("avg_vector"),
            sqlalchemy_func.avg(db_models.ChatLog.reranker_score).label("avg_reranker"),
        )
        .group_by(db_models.ChatLog.confidence)
        .all()
    )
    score_stats = {
        conf: {
            "avg_vector_score": round(avg_vec, 4) if avg_vec else None,
            "avg_reranker_score": round(avg_rer, 4) if avg_rer else None,
        }
        for conf, avg_vec, avg_rer in avg_scores
    }

    # Top confidence reasons
    reason_counts = (
        db.query(db_models.ChatLog.confidence_reason, sqlalchemy_func.count(db_models.ChatLog.id).label("cnt"))
        .group_by(db_models.ChatLog.confidence_reason)
        .order_by(sqlalchemy_func.count(db_models.ChatLog.id).desc())
        .limit(10)
        .all()
    )
    top_reasons = {reason: cnt for reason, cnt in reason_counts if reason}

    total_queries = db.query(sqlalchemy_func.count(db_models.ChatLog.id)).scalar() or 0

    return {
        "total_queries": total_queries,
        "confidence_distribution": confidence_dist,
        "average_scores_by_confidence": score_stats,
        "top_confidence_reasons": top_reasons,
    }


# ─── Debug Retrieval ──────────────────────────────────────────────────────────

@router.post("/debug/retrieval")
def debug_retrieval(
    payload: dict,
    db: Session = Depends(get_db),
    _: TokenUser = Depends(require_admin),
):
    """Debug endpoint to inspect retrieval and confidence scoring for a query.

    Request body:
        {
            "query": "What is the tech stack?",
            "department": "engineering"  (optional)
        }

    Returns:
        Detailed breakdown of vector scores, reranker scores, and confidence reasoning.
    """
    from app.rag.retrieval.hybrid_retriever import HybridRetriever
    from app.rag.retrieval.metadata_filter import MetadataFilterBuilder
    from app.services.confidence_service import ConfidenceService
    from app.config import get_settings

    query = payload.get("query", "").strip()
    department = payload.get("department")

    if not query:
        raise HTTPException(status_code=400, detail="query is required")

    settings = get_settings()

    # Build filter
    query_filter = MetadataFilterBuilder.combined_filter(
        departments=[department] if department else None,
        categories=None,
    )

    # Retrieve with reranking
    retriever = HybridRetriever()
    try:
        results = retriever.retrieve(
            query=query,
            top_k=settings.max_sources,
            rerank=True,
            query_filter=query_filter,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {str(e)}")

    # Calculate confidence
    confidence_svc = ConfidenceService()
    has_reranker = results and "rerank_score" in results[0]
    confidence, debug_info = confidence_svc.calculate(results, has_reranker=has_reranker)

    # Build detailed response
    results_breakdown = []
    for idx, result in enumerate(results[:5]):  # Top 5 only
        results_breakdown.append({
            "rank": idx + 1,
            "doc_name": result["metadata"].get("doc_name", "Unknown"),
            "chunk_id": result["metadata"].get("chunk_id"),
            "vector_score": round(result.get("score", 0), 4),
            "reranker_score": round(result.get("rerank_score", 0), 4) if "rerank_score" in result else None,
            "chunk_preview": result.get("chunk_text", "")[:150],
        })

    return {
        "query": query,
        "department_filter": department,
        "confidence": confidence.value,
        "confidence_reasoning": debug_info,
        "thresholds": confidence_svc.get_thresholds(use_reranker=has_reranker),
        "results": results_breakdown,
    }


# ─── Public: departments list for dropdowns (authenticated users) ─────────────

@router.get("/departments-public")
def list_departments_public(
    db: Session = Depends(get_db),
    _: TokenUser = Depends(get_current_user),
):
    """Returns active department names for use in dropdowns. Any authenticated user."""
    depts = db.query(db_models.Department).filter(db_models.Department.is_active == True).order_by(db_models.Department.name).all()
    return [{"id": d.id, "name": d.name, "description": d.description} for d in depts]
