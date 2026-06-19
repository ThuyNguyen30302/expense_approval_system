"""create users table

Revision ID: 20260619_0001
Revises:
Create Date: 2026-06-19
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


revision: str = "20260619_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("manager_id", sa.Uuid(), nullable=True),
        sa.Column("department", sa.String(length=120), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("deactivated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("email <> ''", name="ck_users_email_not_empty"),
        sa.CheckConstraint(
            "role IN ('employee', 'manager', 'accountant', 'admin')",
            name="ck_users_role",
        ),
        sa.CheckConstraint(
            "manager_id IS NULL OR manager_id <> id",
            name="ck_users_manager_not_self",
        ),
        sa.ForeignKeyConstraint(["manager_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("idx_users_role", "users", ["role"])
    op.create_index("idx_users_manager_id", "users", ["manager_id"])
    op.create_index("idx_users_department", "users", ["department"])
    op.create_index("idx_users_is_active", "users", ["is_active"])


def downgrade() -> None:
    op.drop_index("idx_users_is_active", table_name="users")
    op.drop_index("idx_users_department", table_name="users")
    op.drop_index("idx_users_manager_id", table_name="users")
    op.drop_index("idx_users_role", table_name="users")
    op.drop_table("users")
