from sqlalchemy.orm import Session

from app.models import db_models
from app.models.schemas import FeedbackRequest


def record_feedback(db: Session, payload: FeedbackRequest) -> db_models.Feedback:
    feedback = db_models.Feedback(
        session_id=payload.session_id,
        query=payload.query,
        helpful=payload.helpful,
        comment=payload.comment,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback
