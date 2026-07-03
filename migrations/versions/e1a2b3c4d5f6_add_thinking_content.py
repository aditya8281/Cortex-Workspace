"""Add thinking_content column to conversation_messages for reasoning models.

Revision ID: e1a2b3c4d5f6
Revises: d3a9bbd6a0cb
Create Date: 2026-07-01
"""

from alembic import op
import sqlalchemy as sa

revision = "e1a2b3c4d5f6"
down_revision = "d3a9bbd6a0cb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "conversation_messages",
        sa.Column("thinking_content", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("conversation_messages", "thinking_content")
