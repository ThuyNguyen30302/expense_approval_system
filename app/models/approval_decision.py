import enum
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import utc_now


class ApprovalStage(str, enum.Enum):
    MANAGER = "manager"
    ACCOUNTING = "accounting"


class ApprovalDecisionType(str, enum.Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    RETURNED = "returned"


class ApprovalDecision(Base):
    __tablename__ = "approval_decisions"
    __table_args__ = (
        CheckConstraint("stage IN ('manager', 'accounting')", name="ck_approval_decisions_stage"),
        CheckConstraint("decision IN ('approved', 'rejected', 'returned')", name="ck_approval_decisions_decision"),
        CheckConstraint(
            "decision = 'approved' OR reason IS NOT NULL",
            name="ck_approval_decisions_reason_required",
        ),
        Index("idx_approval_decisions_expense_id", "expense_id"),
        Index("idx_approval_decisions_actor_id", "actor_id"),
        Index("idx_approval_decisions_stage", "stage"),
        Index("idx_approval_decisions_expense_created_at", "expense_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    expense_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("expenses.id"), nullable=False)
    actor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    stage: Mapped[str] = mapped_column(String(32), nullable=False)
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    from_status: Mapped[str] = mapped_column(String(40), nullable=False)
    to_status: Mapped[str] = mapped_column(String(40), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    expense = relationship("Expense")
    actor = relationship("User")
