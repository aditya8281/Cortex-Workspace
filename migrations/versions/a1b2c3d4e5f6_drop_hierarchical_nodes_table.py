"""Drop hierarchical_nodes table (RAG pipeline removed).

The HierarchicalNode model and its table were part of the RAG pipeline
which has been completely removed from the codebase.  This migration
drops the table and its indexes.

Revision ID: a1b2c3d4e5f6
Revises: f7a8b9c0d1e2
Create Date: 2026-06-07
"""

from alembic import op
import sqlalchemy as sa

revision = "a1b2c3d4e5f6"
down_revision = "f7a8b9c0d1e2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index(op.f("ix_hierarchical_nodes_path"), table_name="hierarchical_nodes")
    op.drop_index(op.f("ix_hierarchical_nodes_parent_id"), table_name="hierarchical_nodes")
    op.drop_index(op.f("ix_hierarchical_nodes_node_type"), table_name="hierarchical_nodes")
    op.drop_index(op.f("ix_hierarchical_nodes_id"), table_name="hierarchical_nodes")
    op.drop_table("hierarchical_nodes")


def downgrade() -> None:
    op.create_table(
        "hierarchical_nodes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("node_type", sa.String(length=32), nullable=False),
        sa.Column("path", sa.String(length=1024), nullable=False),
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("hierarchical_nodes.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("hash", sa.String(length=64), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)")),
    )
    op.create_index(op.f("ix_hierarchical_nodes_id"), "hierarchical_nodes", ["id"], unique=False)
    op.create_index(op.f("ix_hierarchical_nodes_node_type"), "hierarchical_nodes", ["node_type"], unique=False)
    op.create_index(op.f("ix_hierarchical_nodes_parent_id"), "hierarchical_nodes", ["parent_id"], unique=False)
    op.create_index(op.f("ix_hierarchical_nodes_path"), "hierarchical_nodes", ["path"], unique=True)
