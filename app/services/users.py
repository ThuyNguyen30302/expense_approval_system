from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import hash_password
from app.models.user import User
from app.repositories.users import UserRepository
from app.schemas.user import AdminUserCreate, UserUpdate
from app.services.auth import normalize_email


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)

    def create_user(self, request: AdminUserCreate) -> User:
        email = normalize_email(request.email)
        self._ensure_email_available(email)
        self._validate_manager(request.manager_id)

        user = User(
            email=email,
            full_name=request.full_name,
            hashed_password=hash_password(request.password),
            role=request.role.value,
            manager_id=request.manager_id,
            department=request.department,
            is_active=request.is_active,
            deactivated_at=None if request.is_active else datetime.now(timezone.utc),
        )
        try:
            created_user = self.users.create(user)
            self.db.commit()
            self.db.refresh(created_user)
            return created_user
        except IntegrityError as exc:
            self.db.rollback()
            raise self._duplicate_email_error() from exc

    def list_users(
        self,
        *,
        limit: int,
        offset: int,
        role: str | None = None,
        is_active: bool | None = None,
    ) -> tuple[list[User], int]:
        return self.users.list(
            limit=limit,
            offset=offset,
            role=role,
            is_active=is_active,
        )

    def get_user(self, user_id: UUID) -> User:
        user = self.users.get_by_id(user_id)
        if user is None:
            raise AppError(
                status_code=404,
                code="user_not_found",
                message="User was not found.",
            )
        return user

    def get_user_for_request(self, user_id: UUID, current_user: User) -> User:
        if current_user.role == "admin" or current_user.id == user_id:
            return self.get_user(user_id)
        raise AppError(
            status_code=403,
            code="auth_forbidden",
            message="You do not have permission to perform this action.",
        )

    def update_user(self, user_id: UUID, request: UserUpdate) -> User:
        user = self.get_user(user_id)
        data = request.model_dump(exclude_unset=True)

        if "email" in data and data["email"] is not None:
            email = normalize_email(data["email"])
            existing_user = self.users.get_by_email(email)
            if existing_user is not None and existing_user.id != user.id:
                raise self._duplicate_email_error()
            user.email = email

        if "password" in data and data["password"] is not None:
            user.hashed_password = hash_password(data["password"])
        if "full_name" in data and data["full_name"] is not None:
            user.full_name = data["full_name"]
        if "role" in data and data["role"] is not None:
            user.role = data["role"].value
        if "manager_id" in data:
            self._validate_manager(data["manager_id"], target_user_id=user.id)
            user.manager_id = data["manager_id"]
        if "department" in data:
            user.department = data["department"]
        if "is_active" in data and data["is_active"] is not None:
            user.is_active = data["is_active"]
            user.deactivated_at = None if user.is_active else datetime.now(timezone.utc)

        try:
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError as exc:
            self.db.rollback()
            raise self._duplicate_email_error() from exc

    def deactivate_user(self, user_id: UUID) -> User:
        user = self.get_user(user_id)
        user.is_active = False
        user.deactivated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(user)
        return user

    def _validate_manager(
        self,
        manager_id: UUID | None,
        target_user_id: UUID | None = None,
    ) -> None:
        if manager_id is None:
            return
        if target_user_id is not None and manager_id == target_user_id:
            raise AppError(
                status_code=400,
                code="user_invalid_manager",
                message="A user cannot be their own manager.",
            )
        if self.users.get_by_id(manager_id) is None:
            raise AppError(
                status_code=400,
                code="user_invalid_manager",
                message="Manager user was not found.",
            )

    def _ensure_email_available(self, email: str) -> None:
        if self.users.get_by_email(email) is not None:
            raise self._duplicate_email_error()

    def _duplicate_email_error(self) -> AppError:
        return AppError(
            status_code=409,
            code="user_email_conflict",
            message="A user with this email already exists.",
        )
