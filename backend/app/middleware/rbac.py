from typing import Callable, List

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.config import get_settings
from app.models.schemas import Department, Role, TokenUser


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenUser:
    settings = get_settings()
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username = payload.get("sub")
        role = payload.get("role")
        departments = payload.get("departments_allowed", [])
        if not username or not role:
            raise credentials_error
    except JWTError as exc:
        raise credentials_error from exc

    return TokenUser(
        username=username,
        role=Role(role),
        departments_allowed=[Department(dept) for dept in departments],
    )


def require_admin(current_user: TokenUser = Depends(get_current_user)) -> TokenUser:
    if current_user.role != Role.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can perform this action",
        )
    return current_user


def require_roles(*roles: Role) -> Callable[[TokenUser], TokenUser]:
    def dependency(current_user: TokenUser = Depends(get_current_user)) -> TokenUser:
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return current_user

    return dependency


def allowed_departments(current_user: TokenUser, requested: Department | None = None) -> List[Department]:
    if requested is None:
        return current_user.departments_allowed

    if requested not in current_user.departments_allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to the requested department",
        )
    return [requested]
