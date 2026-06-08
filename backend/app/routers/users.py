from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.middleware.rbac import get_current_user
from app.models.db_models import get_db, User
from app.models.schemas import Department, Role, TokenUser, UserProfile

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserProfile)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(get_current_user),
):
    user = db.query(User).filter(User.username == current_user.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return UserProfile(
        id=user.id,
        username=user.username,
        role=Role(user.role),
        departments_allowed=[Department(d) for d in user.departments_allowed.split(",")],
        created_at=user.created_at,
    )
