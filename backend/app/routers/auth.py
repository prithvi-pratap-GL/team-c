from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.models.db_models import get_db
from app.models.schemas import LoginRequest, LoginResponse, Role
from app.services.auth_service import authenticate_user, create_access_token
from app.services.audit_service import AuditAction, log_event


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.username, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Block disabled users
    if user.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled. Contact your administrator.",
        )

    ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
    log_event(db, user.username, AuditAction.LOGIN, ip_address=ip)

    return LoginResponse(
        access_token=create_access_token(user),
        role=Role(user.role),
        departments_allowed=user.departments_allowed.split(","),
    )
