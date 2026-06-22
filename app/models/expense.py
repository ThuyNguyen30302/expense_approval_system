import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import utc_now


class ExpenseStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    MANAGER_APPROVED = "manager_approved"
    MANAGER_REJECTED = "manager_rejected"
    RETURNED_TO_EMPLOYEE = "returned_to_employee"
    ACCOUNTANT_APPROVED = "accountant_approved"
    ACCOUNTANT_REJECTED = "accountant_rejected"
    PAYMENT_PENDING = "payment_pending"
    PAID = "paid"
    CANCELLED = "cancelled"


class ExpenseCategory(str, enum.Enum):
    TRAVEL = "travel"
    MEALS = "meals"
    LODGING = "lodging"
    OFFICE_SUPPLIES = "office_supplies"
    SOFTWARE = "software"
    TRAINING = "training"
    TRANSPORTATION = "transportation"
    OTHER = "other"


class Expense(Base):
    __tablename__ = "expenses"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_expenses_amount_positive"),
        CheckConstraint(
            "currency ~ '^[A-Z]{3}$'",
            name="ck_expenses_currency_code",
        ).ddl_if(dialect="postgresql"),
        CheckConstraint(
            "status IN ('draft', 'submitted', 'manager_approved', 'manager_rejected', "
            "'returned_to_employee', 'accountant_approved', 'accountant_rejected', "
            "'payment_pending', 'paid', 'cancelled')",
            name="ck_expenses_status",
        ),
        CheckConstraint(
            "category IN ('travel', 'meals', 'lodging', 'office_supplies', 'software', "
            "'training', 'transportation', 'other')",
            name="ck_expenses_category",
        ),
        CheckConstraint("title <> ''", name="ck_expenses_title_not_empty"),
        CheckConstraint("status <> 'paid' OR paid_at IS NOT NULL", name="ck_expenses_paid_at"),
        Index("idx_expenses_requester_id", "requester_id"),
        Index("idx_expenses_assigned_manager_id", "assigned_manager_id"),
        Index("idx_expenses_status", "status"),
        Index("idx_expenses_category", "category"),
        Index("idx_expenses_expense_date", "expense_date"),
        Index("idx_expenses_created_at", "created_at"),
        Index("idx_expenses_requester_status", "requester_id", "status"),
        Index("idx_expenses_assigned_manager_status", "assigned_manager_id", "status"),
        Index("idx_expenses_status_expense_date", "status", "expense_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    requester_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    assigned_manager_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default=ExpenseStatus.DRAFT.value,
    )
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    department: Mapped[str | None] = mapped_column(String(120))
    project_code: Mapped[str | None] = mapped_column(String(80))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    manager_decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    accountant_decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    requester = relationship("User", foreign_keys=[requester_id], back_populates="expenses")
    assigned_manager = relationship("User", foreign_keys=[assigned_manager_id])
    receipts: Mapped[list["ExpenseReceipt"]] = relationship(
        "ExpenseReceipt",
        back_populates="expense",
        cascade="all, delete-orphan",
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="expense",
    )
