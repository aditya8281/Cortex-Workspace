"""Add embedding_id, tags, vector_collection to knowledge_entries.

Revision ID: i00000000009
Revises: h00000000008
Create Date: 2026-06-19 14:30:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "i00000000009"
down_revision: str | None = "h00000000008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "knowledge_entries",
        sa.Column("embedding_id", sa.String(128), nullable=True, index=True),
    )
    op.add_column(
        "knowledge_entries",
        sa.Column("tags", sa.Text, nullable=True),
    )
    op.add_column(
        "knowledge_entries",
        sa.Column(
            "vector_collection",
            sa.String(64),
            nullable=False,
            server_default="cortex_memory",
        ),
    )


def downgrade() -> None:
    op.drop_column("knowledge_entries", "vector_collection")
    op.drop_column("knowledge_entries", "tags")
    op.drop_column("knowledge_entries", "embedding_id")
