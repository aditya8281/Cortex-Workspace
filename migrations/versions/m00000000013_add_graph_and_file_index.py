"""Add graph_nodes, graph_edges, and indexed_files tables.

Revision ID: m00000000013
Revises: l00000000012
Create Date: 2026-06-20 12:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "m00000000013"
down_revision: str | None = "l00000000012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── graph_nodes ──────────────────────────────────────────────
    op.create_table(
        "graph_nodes",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "chunk_id",
            sa.Integer(),
            sa.ForeignKey("code_chunks.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "repo_id",
            sa.Integer(),
            sa.ForeignKey("repo_indexes.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("node_type", sa.String(50), nullable=False, index=True),
        sa.Column("name", sa.String(500), nullable=False, index=True),
        sa.Column("qualified_name", sa.String(1000), nullable=True),
        sa.Column("language", sa.String(50), nullable=True),
        sa.Column("file_path", sa.String(2000), nullable=False, index=True),
        sa.Column("start_line", sa.Integer(), nullable=True),
        sa.Column("end_line", sa.Integer(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_graph_nodes_file_type", "graph_nodes", ["file_path", "node_type"])
    op.create_index("idx_graph_nodes_qualified", "graph_nodes", ["qualified_name"])

    # ── graph_edges ──────────────────────────────────────────────
    op.create_table(
        "graph_edges",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "source_id",
            sa.Integer(),
            sa.ForeignKey("graph_nodes.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "target_id",
            sa.Integer(),
            sa.ForeignKey("graph_nodes.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("edge_type", sa.String(50), nullable=False, index=True),
        sa.Column("weight", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_graph_edges_source_type", "graph_edges", ["source_id", "edge_type"])
    op.create_index("idx_graph_edges_target_type", "graph_edges", ["target_id", "edge_type"])

    # ── indexed_files ────────────────────────────────────────────
    op.create_table(
        "indexed_files",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "repo_id",
            sa.Integer(),
            sa.ForeignKey("repo_indexes.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("file_path", sa.String(2000), nullable=False),
        sa.Column("file_hash", sa.String(64), nullable=False),
        sa.Column("last_indexed_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="indexed"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_indexed_files_repo_path", "indexed_files", ["repo_id", "file_path"], unique=True)


def downgrade() -> None:
    op.drop_table("indexed_files")
    op.drop_table("graph_edges")
    op.drop_table("graph_nodes")
