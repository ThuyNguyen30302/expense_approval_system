from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        self.db.refresh(user)
        return user

    def get_by_id(self, user_id: UUID) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        return self.db.execute(statement).scalar_one_or_none()

    def list(
        self,
        *,
        limit: int,
        offset: int,
        role: str | None = None,
        is_active: bool | None = None,
    ) -> tuple[list[User], int]:
        statement = self._filtered_select(role=role, is_active=is_active)
        count_statement = select(func.count()).select_from(
            self._filtered_select(role=role, is_active=is_active).subquery()
        )

        users = self.db.execute(
            statement.order_by(User.created_at.desc()).limit(limit).offset(offset)
        ).scalars().all()
        total = self.db.execute(count_statement).scalar_one()
        return list(users), total

    def _filtered_select(
        self,
        *,
        role: str | None,
        is_active: bool | None,
    ) -> Select[tuple[User]]:
        statement = select(User)
        if role is not None:
            statement = statement.where(User.role == role)
        if is_active is not None:
            statement = statement.where(User.is_active.is_(is_active))
        return statement
