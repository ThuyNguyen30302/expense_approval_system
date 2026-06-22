import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import utc_now


class ExpenseReceipt(Base):
    __tablename__ = "expense_receipts"
    __table_args__ = (
        CheckConstraint(
            "size_bytes IS NULL OR size_bytes > 0",
            name="ck_expense_receipts_size_positive",
        ),
        CheckConstraint(
            "url IS NOT NULL OR file_name IS NOT NULL OR metadata IS NOT NULL",
            name="ck_expense_receipts_has_reference",
        ),
        Index("idx_expense_receipts_expense_id", "expense_id"),
        Index("idx_expense_receipts_uploaded_by_id", "uploaded_by_id"),
        Index("idx_expense_receipts_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    expense_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("expenses.id"), nullable=False)
    uploaded_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    url: Mapped[str | None] = mapped_column(Text)
    file_name: Mapped[str | None] = mapped_column(String(255))
    content_type: Mapped[str | None] = mapped_column(String(120))
    size_bytes: Mapped[int | None] = mapped_column(Integer)
    checksum: Mapped[str | None] = mapped_column(String(128))
    receipt_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSONB().with_variant(JSON(), "sqlite"),
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    expense = relationship("Expense", back_populates="receipts")
    uploaded_by = relationship("User")
