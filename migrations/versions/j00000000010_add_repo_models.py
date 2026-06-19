"""Add repo_indexes and code_chunks tables for repository scanning.

Revision ID: j00000000010
Revises: i00000000009
Create Date: 2026-06-19 18:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "j00000000010"
down_revision: str | None = "i00000000009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "repo_indexes",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), nullable=True, index=True),
        sa.Column("repo_path", sa.String(2048), nullable=False, unique=True),
        sa.Column("repo_name", sa.String(256), nullable=False),
        sa.Column("primary_language", sa.String(64), nullable=True),
        sa.Column("total_files", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_chunks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_commit", sa.String(64), nullable=True),
        sa.Column("last_indexed_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "code_chunks",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("repo_id", sa.Integer(), nullable=False, index=True),
        sa.Column("file_path", sa.String(2048), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("language", sa.String(64), nullable=True),
        sa.Column("symbol_type", sa.String(64), nullable=True),
        sa.Column("symbol_name", sa.String(256), nullable=True, index=True),
        sa.Column("start_line", sa.Integer(), nullable=True),
        sa.Column("end_line", sa.Integer(), nullable=True),
        sa.Column("embedding_id", sa.String(128), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("code_chunks")
    op.drop_table("repo_indexes")
