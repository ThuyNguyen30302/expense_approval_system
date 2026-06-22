"""create approval and payment tables

Revision ID: 20260622_0003
Revises: 20260622_0002
Create Date: 2026-06-22
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


revision: str = "20260622_0003"
down_revision: str | None = "20260622_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "approval_decisions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("expense_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("stage", sa.String(length=32), nullable=False),
        sa.Column("decision", sa.String(length=32), nullable=False),
        sa.Column("from_status", sa.String(length=40), nullable=False),
        sa.Column("to_status", sa.String(length=40), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("stage IN ('manager', 'accounting')", name="ck_approval_decisions_stage"),
        sa.CheckConstraint("decision IN ('approved', 'rejected', 'returned')", name="ck_approval_decisions_decision"),
        sa.CheckConstraint(
            "decision = 'approved' OR reason IS NOT NULL",
            name="ck_approval_decisions_reason_required",
        ),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["expense_id"], ["expenses.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_approval_decisions_expense_id", "approval_decisions", ["expense_id"])
    op.create_index("idx_approval_decisions_actor_id", "approval_decisions", ["actor_id"])
    op.create_index("idx_approval_decisions_stage", "approval_decisions", ["stage"])
    op.create_index("idx_approval_decisions_expense_created_at", "approval_decisions", ["expense_id", "created_at"])

    op.create_table(
        "payments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("expense_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("payment_method", sa.String(length=40), nullable=True),
        sa.Column("payment_reference", sa.String(length=120), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("status IN ('payment_pending', 'paid')", name="ck_payments_status"),
        sa.CheckConstraint(
            "payment_method IS NULL OR payment_method IN "
            "('bank_transfer', 'check', 'cash', 'corporate_card', 'other')",
            name="ck_payments_payment_method",
        ),
        sa.CheckConstraint("status <> 'paid' OR paid_at IS NOT NULL", name="ck_payments_paid_at"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["expense_id"], ["expenses.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_payments_expense_id", "payments", ["expense_id"])
    op.create_index("idx_payments_actor_id", "payments", ["actor_id"])
    op.create_index("idx_payments_status", "payments", ["status"])
    op.create_index("idx_payments_paid_at", "payments", ["paid_at"])


def downgrade() -> None:
    op.drop_index("idx_payments_paid_at", table_name="payments")
    op.drop_index("idx_payments_status", table_name="payments")
    op.drop_index("idx_payments_actor_id", table_name="payments")
    op.drop_index("idx_payments_expense_id", table_name="payments")
    op.drop_table("payments")

    op.drop_index("idx_approval_decisions_expense_created_at", table_name="approval_decisions")
    op.drop_index("idx_approval_decisions_stage", table_name="approval_decisions")
    op.drop_index("idx_approval_decisions_actor_id", table_name="approval_decisions")
    op.drop_index("idx_approval_decisions_expense_id", table_name="approval_decisions")
    op.drop_table("approval_decisions")
