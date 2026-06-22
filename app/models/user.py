import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UserRole(str, enum.Enum):
    EMPLOYEE = "employee"
    MANAGER = "manager"
    ACCOUNTANT = "accountant"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("email <> ''", name="ck_users_email_not_empty"),
        CheckConstraint(
            "role IN ('employee', 'manager', 'accountant', 'admin')",
            name="ck_users_role",
        ),
        CheckConstraint(
            "manager_id IS NULL OR manager_id <> id",
            name="ck_users_manager_not_self",
        ),
        Index("idx_users_role", "role"),
        Index("idx_users_manager_id", "manager_id"),
        Index("idx_users_department", "department"),
        Index("idx_users_is_active", "is_active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default=UserRole.EMPLOYEE.value)
    manager_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    department: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
    deactivated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    manager: Mapped["User | None"] = relationship(
        "User",
        remote_side=[id],
        back_populates="direct_reports",
    )
    direct_reports: Mapped[list["User"]] = relationship(
        "User",
        back_populates="manager",
    )
    expenses: Mapped[list["Expense"]] = relationship(
        "Expense",
        foreign_keys="Expense.requester_id",
        back_populates="requester",
    )
