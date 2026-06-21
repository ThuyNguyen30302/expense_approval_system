from collections.abc import Callable, Generator
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import decode_access_token
from app.db.session import get_db_session
from app.models.user import User, UserRole
from app.repositories.users import UserRepository


bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    yield from get_db_session()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise AppError(
            status_code=401,
            code="auth_not_authenticated",
            message="Authentication credentials were not provided.",
        )

    token = credentials.credentials
    payload = decode_access_token(token)
    try:
        user_id = UUID(str(payload["sub"]))
    except ValueError as exc:
        raise AppError(
            status_code=401,
            code="auth_invalid_token",
            message="Invalid authentication credentials.",
        ) from exc

    user = UserRepository(db).get_by_id(user_id)
    if user is None:
        raise AppError(
            status_code=401,
            code="auth_invalid_token",
            message="Invalid authentication credentials.",
        )

    return user


def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    if not user.is_active:
        raise AppError(
            status_code=401,
            code="auth_inactive_user",
            message="Invalid authentication credentials.",
        )
    return user


def require_roles(*allowed_roles: UserRole) -> Callable[[User], User]:
    allowed_values = {role.value for role in allowed_roles}

    def dependency(user: User = Depends(get_current_active_user)) -> User:
        if user.role not in allowed_values:
            raise AppError(
                status_code=403,
                code="auth_forbidden",
                message="You do not have permission to perform this action.",
            )
        return user

    return dependency


def require_admin(user: User = Depends(require_roles(UserRole.ADMIN))) -> User:
    return user
