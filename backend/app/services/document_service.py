from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import db_models
from app.models.schemas import Department


def list_documents(
    db: Session,
    departments: List[Department],
    category: Optional[str],
    page: int,
    page_size: int,
) -> tuple[List[db_models.Document], int]:
    query = db.query(db_models.Document).filter(
        db_models.Document.department.in_([dept.value for dept in departments])
    )
    if category:
        query = query.filter(db_models.Document.category == category)

    total = query.count()
    documents = (
        query.order_by(db_models.Document.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return documents, total
