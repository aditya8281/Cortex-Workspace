"""Fix document_type enum and create long_term_memories table.

Revision ID: z00000000025
Revises: y00000000024
Create Date: 2026-06-22
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "z00000000025"
down_revision: str | None = "y00000000024"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Fix document_type enum — add missing values
    missing_types = [
        "docx",
        "epub",
        "html",
        "pptx",
        "xlsx",
        "opendocument",
        "vcard",
        "ical",
        "archive",
        "image",
        "audio",
        "video",
        "font",
        "gis",
    ]
    for doc_type in missing_types:
        op.execute(f"ALTER TYPE document_type ADD VALUE IF NOT EXISTS '{doc_type}'")

    # Create long_term_memories table
    op.create_table(
        "long_term_memories",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False, index=True),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("access_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_accessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("embedding_id", sa.String(100), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("decayed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("long_term_memories")
    # Note: PostgreSQL doesn't support removing individual enum values
    # The extra values will remain but be unused
