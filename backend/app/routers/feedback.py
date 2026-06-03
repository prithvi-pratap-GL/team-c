from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.middleware.rbac import get_current_user
from app.models.db_models import get_db
from app.models.schemas import FeedbackRequest, FeedbackResponse, TokenUser
from app.services.feedback_service import record_feedback


router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackResponse)
def feedback(
    payload: FeedbackRequest,
    db: Session = Depends(get_db),
    current_user: TokenUser = Depends(get_current_user),
):
    record_feedback(db, payload)
    return FeedbackResponse()
