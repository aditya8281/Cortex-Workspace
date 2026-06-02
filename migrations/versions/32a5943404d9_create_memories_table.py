"""create memories table

Revision ID: 32a5943404d9
Revises: 3a5b9f32d36d
Create Date: 2026-06-02 23:10:40.858015
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "32a5943404d9"
down_revision: Union[str, Sequence[str], None] = "3a5b9f32d36d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "memories",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("query", sa.Text, nullable=False),
        sa.Column("response", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    op.create_index(
        "ix_memories_user_id",
        "memories",
        ["user_id"]
    )

    op.create_index(
        "ix_memories_created_at",
        "memories",
        ["created_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_memories_created_at", table_name="memories")
    op.drop_index("ix_memories_user_id", table_name="memories")
    op.drop_table("memories")