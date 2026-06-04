from datetime import datetime, timedelta
from typing import Dict, List, Optional

from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import db_models
from app.models.schemas import Department, Role


pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

ROLE_DEPARTMENTS: Dict[Role, List[Department]] = {
    Role.admin: [
        Department.engineering,
        Department.hr,
        Department.operations,
        Department.product_support,
    ],
    Role.engineering: [Department.engineering],
    Role.hr: [Department.hr],
    Role.operations: [Department.operations],
    Role.support: [Department.product_support],
}

DEMO_USERS = {
    "admin": ("admin123", Role.admin),
    "alice_hr": ("hr123", Role.hr),
    "bob_eng": ("eng123", Role.engineering),
    "olivia_ops": ("ops123", Role.operations),
    "sam_support": ("support123", Role.support),
}


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def departments_for_role(role: Role) -> List[Department]:
    return ROLE_DEPARTMENTS[role]


def seed_demo_users(db: Session) -> None:
    for username, (password, role) in DEMO_USERS.items():
        existing = db.query(db_models.User).filter(db_models.User.username == username).first()
        if existing:
            continue

        departments = ",".join(dept.value for dept in departments_for_role(role))
        db.add(
            db_models.User(
                username=username,
                password_hash=get_password_hash(password),
                role=role.value,
                departments_allowed=departments,
            )
        )
    db.commit()


def authenticate_user(db: Session, username: str, password: str) -> Optional[db_models.User]:
    user = db.query(db_models.User).filter(db_models.User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def create_access_token(user: db_models.User) -> str:
    settings = get_settings()
    expires_at = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": user.username,
        "role": user.role,
        "departments_allowed": user.departments_allowed.split(","),
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
