"""Add notifications table.

Revision ID: k00000000011
Revises: j00000000010
Create Date: 2026-06-19 20:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "k00000000011"
down_revision: str | None = "j00000000010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("type", sa.String(32), nullable=False, server_default="system"),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_notifications_user_read", "notifications", ["user_id", "read"])


def downgrade() -> None:
    op.drop_index("ix_notifications_user_read")
    op.drop_table("notifications")
