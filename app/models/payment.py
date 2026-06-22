import enum
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import utc_now


class PaymentMethod(str, enum.Enum):
    BANK_TRANSFER = "bank_transfer"
    CHECK = "check"
    CASH = "cash"
    CORPORATE_CARD = "corporate_card"
    OTHER = "other"


class PaymentStatus(str, enum.Enum):
    PAYMENT_PENDING = "payment_pending"
    PAID = "paid"


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("status IN ('payment_pending', 'paid')", name="ck_payments_status"),
        CheckConstraint(
            "payment_method IS NULL OR payment_method IN "
            "('bank_transfer', 'check', 'cash', 'corporate_card', 'other')",
            name="ck_payments_payment_method",
        ),
        CheckConstraint("status <> 'paid' OR paid_at IS NOT NULL", name="ck_payments_paid_at"),
        Index("idx_payments_expense_id", "expense_id"),
        Index("idx_payments_actor_id", "actor_id"),
        Index("idx_payments_status", "status"),
        Index("idx_payments_paid_at", "paid_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    expense_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("expenses.id"), nullable=False)
    actor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    payment_method: Mapped[str | None] = mapped_column(String(40))
    payment_reference: Mapped[str | None] = mapped_column(String(120))
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    expense = relationship("Expense")
    actor = relationship("User")
