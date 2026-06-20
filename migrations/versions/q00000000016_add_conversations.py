"""add conversations tables

Revision ID: q00000000016
Revises: p00000000015
Create Date: 2026-06-20 15:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "q00000000016"
down_revision: str | None = "p00000000015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("user_id", sa.Integer, nullable=False, index=True),
        sa.Column("title", sa.String(255), server_default="New Conversation"),
        sa.Column("repo_id", sa.Integer, nullable=True),
        sa.Column("model_used", sa.String(100), nullable=True),
        sa.Column("message_count", sa.Integer, server_default="0"),
        sa.Column("total_tokens", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "conversation_messages",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column(
            "conversation_id",
            sa.Integer,
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("metadata_json", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("conversation_messages")
    op.drop_table("conversations")
