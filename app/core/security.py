from datetime import datetime, timedelta, timezone
from hashlib import sha256
from uuid import UUID

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings
from app.core.errors import AppError


def _password_digest(password: str) -> bytes:
    return sha256(password.encode("utf-8")).hexdigest().encode("utf-8")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_password_digest(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(_password_digest(plain_password), hashed_password.encode("utf-8"))


def create_access_token(user_id: UUID, role: str) -> tuple[str, int]:
    settings = get_settings()
    expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    expires_at = datetime.now(timezone.utc) + expires_delta
    expires_in = int(expires_delta.total_seconds())
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "exp": expires_at,
    }
    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return token, expires_in


def decode_access_token(token: str) -> dict[str, str]:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as exc:
        raise AppError(
            status_code=401,
            code="auth_invalid_token",
            message="Invalid authentication credentials.",
        ) from exc

    if payload.get("type") != "access" or payload.get("sub") is None:
        raise AppError(
            status_code=401,
            code="auth_invalid_token",
            message="Invalid authentication credentials.",
        )

    return payload
