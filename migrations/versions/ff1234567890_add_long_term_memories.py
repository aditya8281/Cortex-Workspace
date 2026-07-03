"""Ensure long_term_memories table exists.

The table was defined in the baseline migration (b00000000000) but
was not created in some environments due to migration ordering issues.
This migration guarantees its existence regardless of prior state.

Revision ID: ff1234567890
Revises: e1a2b3c4d5f6
Create Date: 2026-07-02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "ff1234567890"
down_revision: Union[str, None] = "e1a2b3c4d5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if not inspector.has_table("long_term_memories"):
        op.create_table(
            "long_term_memories",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("category", sa.String(length=50), nullable=False),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
            sa.Column("access_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("last_accessed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("source", sa.String(length=100), nullable=True),
            sa.Column("source_id", sa.Integer(), nullable=True),
            sa.Column("embedding_id", sa.String(length=100), nullable=True),
            sa.Column("tags", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("decayed_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_long_term_memories_user_id", "long_term_memories", ["user_id"]
        )
        op.create_index(
            "ix_long_term_memories_user_id_category",
            "long_term_memories",
            ["user_id", "category"],
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if inspector.has_table("long_term_memories"):
        op.drop_table("long_term_memories")
