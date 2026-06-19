from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User, UserRole
from app.repositories.users import UserRepository
from app.schemas.auth import RegisterRequest, TokenResponse


def normalize_email(email: str) -> str:
    return email.strip().lower()


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)

    def register(self, request: RegisterRequest) -> User:
        email = normalize_email(request.email)
        self._ensure_email_available(email)

        user = User(
            email=email,
            full_name=request.full_name,
            hashed_password=hash_password(request.password),
            role=UserRole.EMPLOYEE.value,
            is_active=True,
        )
        try:
            created_user = self.users.create(user)
            self.db.commit()
            self.db.refresh(created_user)
            return created_user
        except IntegrityError as exc:
            self.db.rollback()
            raise self._duplicate_email_error() from exc

    def login(self, email: str, password: str) -> TokenResponse:
        user = self.users.get_by_email(normalize_email(email))
        if user is None or not verify_password(password, user.hashed_password):
            raise self._invalid_credentials_error()
        if not user.is_active:
            raise self._invalid_credentials_error()

        access_token, expires_in = create_access_token(user.id, user.role)
        return TokenResponse(access_token=access_token, expires_in=expires_in)

    def _ensure_email_available(self, email: str) -> None:
        if self.users.get_by_email(email) is not None:
            raise self._duplicate_email_error()

    def _duplicate_email_error(self) -> AppError:
        return AppError(
            status_code=409,
            code="user_email_conflict",
            message="A user with this email already exists.",
        )

    def _invalid_credentials_error(self) -> AppError:
        return AppError(
            status_code=401,
            code="auth_invalid_credentials",
            message="Invalid authentication credentials.",
        )
