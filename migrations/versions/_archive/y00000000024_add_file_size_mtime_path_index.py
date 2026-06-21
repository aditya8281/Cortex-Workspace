"""Add file_size/mtime to indexed_files and create path_index table.

Revision ID: y00000000024
Revises: x00000000023
Create Date: 2026-06-22
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "y00000000024"
down_revision: str | None = "x00000000023"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── indexed_files: add file_size and mtime ────────────────────
    op.add_column("indexed_files", sa.Column("file_size", sa.BigInteger(), nullable=True))
    op.add_column("indexed_files", sa.Column("mtime", sa.Float(), nullable=True))

    # ── path_index ───────────────────────────────────────────────
    op.create_table(
        "path_index",
        sa.Column("path", sa.String(2000), primary_key=True),
        sa.Column("parent_path", sa.String(2000), nullable=False, index=True),
        sa.Column("basename", sa.String(256), nullable=False),
        sa.Column("depth", sa.Integer(), nullable=False, index=True),
        sa.Column("is_dir", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("file_count", sa.Integer(), server_default=sa.text("0")),
        sa.Column("total_size", sa.BigInteger(), server_default=sa.text("0")),
        sa.Column("last_modified", sa.DateTime(), nullable=True),
        sa.Column(
            "repo_id",
            sa.Integer(),
            sa.ForeignKey("repo_indexes.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
    )
    op.create_index("idx_path_index_repo_parent", "path_index", ["repo_id", "parent_path"])
    op.create_index("idx_path_index_repo_depth", "path_index", ["repo_id", "depth"])


def downgrade() -> None:
    op.drop_index("idx_path_index_repo_depth", table_name="path_index")
    op.drop_index("idx_path_index_repo_parent", table_name="path_index")
    op.drop_table("path_index")
    op.drop_column("indexed_files", "mtime")
    op.drop_column("indexed_files", "file_size")
