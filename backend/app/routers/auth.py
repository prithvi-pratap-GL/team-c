from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models.db_models import get_db
from app.models.schemas import LoginRequest, LoginResponse, Role
from app.services.auth_service import authenticate_user, create_access_token


router = APIRouter(prefix="/auth", tags=["auth"])


@router.options("/login")
def options_login():
    return {}


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.username, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return LoginResponse(
        access_token=create_access_token(user),
        role=Role(user.role),
        departments_allowed=user.departments_allowed.split(","),
    )
