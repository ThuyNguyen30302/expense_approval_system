"""create expense core tables

Revision ID: 20260622_0002
Revises: 20260619_0001
Create Date: 2026-06-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op


revision: str = "20260622_0002"
down_revision: str | None = "20260619_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "expenses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("requester_id", sa.Uuid(), nullable=False),
        sa.Column("assigned_manager_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=40), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("expense_date", sa.Date(), nullable=False),
        sa.Column("department", sa.String(length=120), nullable=True),
        sa.Column("project_code", sa.String(length=80), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("manager_decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accountant_decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("amount > 0", name="ck_expenses_amount_positive"),
        sa.CheckConstraint("currency ~ '^[A-Z]{3}$'", name="ck_expenses_currency_code"),
        sa.CheckConstraint(
            "status IN ('draft', 'submitted', 'manager_approved', 'manager_rejected', "
            "'returned_to_employee', 'accountant_approved', 'accountant_rejected', "
            "'payment_pending', 'paid', 'cancelled')",
            name="ck_expenses_status",
        ),
        sa.CheckConstraint(
            "category IN ('travel', 'meals', 'lodging', 'office_supplies', 'software', "
            "'training', 'transportation', 'other')",
            name="ck_expenses_category",
        ),
        sa.CheckConstraint("title <> ''", name="ck_expenses_title_not_empty"),
        sa.CheckConstraint("status <> 'paid' OR paid_at IS NOT NULL", name="ck_expenses_paid_at"),
        sa.ForeignKeyConstraint(["assigned_manager_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_expenses_requester_id", "expenses", ["requester_id"])
    op.create_index("idx_expenses_assigned_manager_id", "expenses", ["assigned_manager_id"])
    op.create_index("idx_expenses_status", "expenses", ["status"])
    op.create_index("idx_expenses_category", "expenses", ["category"])
    op.create_index("idx_expenses_expense_date", "expenses", ["expense_date"])
    op.create_index("idx_expenses_created_at", "expenses", ["created_at"])
    op.create_index("idx_expenses_requester_status", "expenses", ["requester_id", "status"])
    op.create_index("idx_expenses_assigned_manager_status", "expenses", ["assigned_manager_id", "status"])
    op.create_index("idx_expenses_status_expense_date", "expenses", ["status", "expense_date"])

    op.create_table(
        "expense_receipts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("expense_id", sa.Uuid(), nullable=False),
        sa.Column("uploaded_by_id", sa.Uuid(), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("file_name", sa.String(length=255), nullable=True),
        sa.Column("content_type", sa.String(length=120), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("size_bytes IS NULL OR size_bytes > 0", name="ck_expense_receipts_size_positive"),
        sa.CheckConstraint(
            "url IS NOT NULL OR file_name IS NOT NULL OR metadata IS NOT NULL",
            name="ck_expense_receipts_has_reference",
        ),
        sa.ForeignKeyConstraint(["expense_id"], ["expenses.id"]),
        sa.ForeignKeyConstraint(["uploaded_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_expense_receipts_expense_id", "expense_receipts", ["expense_id"])
    op.create_index("idx_expense_receipts_uploaded_by_id", "expense_receipts", ["uploaded_by_id"])
    op.create_index("idx_expense_receipts_created_at", "expense_receipts", ["created_at"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("expense_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("event_type", sa.String(length=60), nullable=False),
        sa.Column("previous_status", sa.String(length=40), nullable=True),
        sa.Column("new_status", sa.String(length=40), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "event_type IN ('expense_created', 'expense_updated', 'expense_submitted', "
            "'expense_cancelled', 'receipt_added', 'manager_approved', 'manager_rejected', "
            "'expense_returned', 'accountant_approved', 'accountant_rejected', "
            "'payment_pending', 'expense_paid', 'admin_corrected')",
            name="ck_audit_logs_event_type",
        ),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["expense_id"], ["expenses.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_audit_logs_expense_id", "audit_logs", ["expense_id"])
    op.create_index("idx_audit_logs_actor_id", "audit_logs", ["actor_id"])
    op.create_index("idx_audit_logs_event_type", "audit_logs", ["event_type"])
    op.create_index("idx_audit_logs_created_at", "audit_logs", ["created_at"])
    op.create_index("idx_audit_logs_expense_created_at", "audit_logs", ["expense_id", "created_at"])


def downgrade() -> None:
    op.drop_index("idx_audit_logs_expense_created_at", table_name="audit_logs")
    op.drop_index("idx_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("idx_audit_logs_event_type", table_name="audit_logs")
    op.drop_index("idx_audit_logs_actor_id", table_name="audit_logs")
    op.drop_index("idx_audit_logs_expense_id", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("idx_expense_receipts_created_at", table_name="expense_receipts")
    op.drop_index("idx_expense_receipts_uploaded_by_id", table_name="expense_receipts")
    op.drop_index("idx_expense_receipts_expense_id", table_name="expense_receipts")
    op.drop_table("expense_receipts")

    op.drop_index("idx_expenses_status_expense_date", table_name="expenses")
    op.drop_index("idx_expenses_assigned_manager_status", table_name="expenses")
    op.drop_index("idx_expenses_requester_status", table_name="expenses")
    op.drop_index("idx_expenses_created_at", table_name="expenses")
    op.drop_index("idx_expenses_expense_date", table_name="expenses")
    op.drop_index("idx_expenses_category", table_name="expenses")
    op.drop_index("idx_expenses_status", table_name="expenses")
    op.drop_index("idx_expenses_assigned_manager_id", table_name="expenses")
    op.drop_index("idx_expenses_requester_id", table_name="expenses")
    op.drop_table("expenses")
