"""Audit log service — write and query audit events."""
import json
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models import db_models


# Action constants
class AuditAction:
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    USER_CREATE = "USER_CREATE"
    USER_UPDATE = "USER_UPDATE"
    USER_DELETE = "USER_DELETE"
    USER_DISABLE = "USER_DISABLE"
    ROLE_CHANGE = "ROLE_CHANGE"
    DEPT_CHANGE = "DEPT_CHANGE"
    DOC_UPLOAD = "DOC_UPLOAD"
    DOC_DELETE = "DOC_DELETE"
    DOC_REINGEST = "DOC_REINGEST"
    DEPT_CREATE = "DEPT_CREATE"
    DEPT_UPDATE = "DEPT_UPDATE"


def log_event(
    db: Session,
    actor: str,
    action: str,
    target: Optional[str] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
) -> None:
    """Write an audit log entry to the database."""
    entry = db_models.AuditLog(
        timestamp=datetime.utcnow(),
        actor=actor,
        action=action,
        target=target,
        details=json.dumps(details) if details else None,
        ip_address=ip_address,
    )
    db.add(entry)
    db.commit()
