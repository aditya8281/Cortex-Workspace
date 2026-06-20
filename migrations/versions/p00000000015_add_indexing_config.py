"""add indexing configs table

Revision ID: p00000000015
Revises: n00000000014
Create Date: 2026-06-20 15:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "p00000000015"
down_revision: str | None = "n00000000014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "indexing_configs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("name", sa.String(255), server_default="default"),
        sa.Column("include_paths", sa.JSON, nullable=True),
        sa.Column("exclude_paths", sa.JSON, nullable=True),
        sa.Column("include_patterns", sa.JSON, nullable=True),
        sa.Column("exclude_patterns", sa.JSON, nullable=True),
        sa.Column("max_file_size_bytes", sa.Integer, server_default="1000000"),
        sa.Column("follow_symlinks", sa.Boolean, server_default="false"),
        sa.Column("sync_enabled", sa.Boolean, server_default="true"),
        sa.Column("sync_interval_seconds", sa.Integer, server_default="300"),
        sa.Column("priority", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("indexing_configs")
