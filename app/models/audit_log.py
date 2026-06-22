import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import utc_now


class AuditEventType(str, enum.Enum):
    EXPENSE_CREATED = "expense_created"
    EXPENSE_UPDATED = "expense_updated"
    EXPENSE_SUBMITTED = "expense_submitted"
    EXPENSE_CANCELLED = "expense_cancelled"
    RECEIPT_ADDED = "receipt_added"
    MANAGER_APPROVED = "manager_approved"
    MANAGER_REJECTED = "manager_rejected"
    EXPENSE_RETURNED = "expense_returned"
    ACCOUNTANT_APPROVED = "accountant_approved"
    ACCOUNTANT_REJECTED = "accountant_rejected"
    PAYMENT_PENDING = "payment_pending"
    EXPENSE_PAID = "expense_paid"
    ADMIN_CORRECTED = "admin_corrected"


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        CheckConstraint(
            "event_type IN ('expense_created', 'expense_updated', 'expense_submitted', "
            "'expense_cancelled', 'receipt_added', 'manager_approved', 'manager_rejected', "
            "'expense_returned', 'accountant_approved', 'accountant_rejected', "
            "'payment_pending', 'expense_paid', 'admin_corrected')",
            name="ck_audit_logs_event_type",
        ),
        Index("idx_audit_logs_expense_id", "expense_id"),
        Index("idx_audit_logs_actor_id", "actor_id"),
        Index("idx_audit_logs_event_type", "event_type"),
        Index("idx_audit_logs_created_at", "created_at"),
        Index("idx_audit_logs_expense_created_at", "expense_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    expense_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("expenses.id"), nullable=False)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    event_type: Mapped[str] = mapped_column(String(60), nullable=False)
    previous_status: Mapped[str | None] = mapped_column(String(40))
    new_status: Mapped[str | None] = mapped_column(String(40))
    comment: Mapped[str | None] = mapped_column(Text)
    audit_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSONB().with_variant(JSON(), "sqlite"),
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    expense = relationship("Expense", back_populates="audit_logs")
    actor = relationship("User")
