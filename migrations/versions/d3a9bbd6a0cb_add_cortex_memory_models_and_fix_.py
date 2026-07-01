"""add_cortex_memory_models_and_fix_snapshot_columns

Creates missing cortex memory domain tables:
  - episodic_memories
  - working_memories
  - semantic_memories
  - memory_nodes (+ indexes, FK)
  - memory_edges (+ indexes, FK)

Also fixes system_snapshots column types:
  - network_sent_bytes: Integer → BigInteger
  - network_recv_bytes: Integer → BigInteger

Revision ID: d3a9bbd6a0cb
Revises: 192f11692f6e
Create Date: 2026-07-01 20:04:44.047166

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers, used by Alembic.
revision: str = "d3a9bbd6a0cb"
down_revision: Union[str, Sequence[str], None] = "192f11692f6e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Fix system_snapshots: Integer → BigInteger ──────────────────
    with op.batch_alter_table("system_snapshots", schema=None) as batch_op:
        batch_op.alter_column(
            "network_sent_bytes",
            existing_type=sa.Integer(),
            type_=sa.BigInteger(),
            existing_nullable=False,
            existing_server_default=None,
        )
        batch_op.alter_column(
            "network_recv_bytes",
            existing_type=sa.Integer(),
            type_=sa.BigInteger(),
            existing_nullable=False,
            existing_server_default=None,
        )

    # ── Episodic memories ──────────────────────────────────────────
    op.create_table(
        "episodic_memories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("context", JSON(), nullable=True),
        sa.Column("emotion", sa.String(50), nullable=True),
        sa.Column("importance", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("access_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_accessed", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("temporal_context", JSON(), nullable=True),
        sa.Column("recency_score", sa.Float(), nullable=False, server_default="1.0"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("episodic_memories", schema=None) as batch_op:
        batch_op.create_index("ix_episodic_user_created", ["user_id", "created_at"])
        batch_op.create_index("ix_episodic_user_importance", ["user_id", "importance"])
        batch_op.create_index("ix_episodic_user_confidence", ["user_id", "confidence"])
        batch_op.create_index("ix_episodic_user_recency", ["user_id", "recency_score"])
        batch_op.create_index("ix_episodic_memories_user_id", ["user_id"])

    # ── Working memories ───────────────────────────────────────────
    op.create_table(
        "working_memories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("session_id", sa.String(100), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("slot", sa.String(50), nullable=False, server_default="active"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("working_memories", schema=None) as batch_op:
        batch_op.create_index("ix_working_memories_user_id", ["user_id"])
        batch_op.create_index("ix_working_user_session", ["user_id", "session_id"])
        batch_op.create_index(
            "ix_working_user_session_slot",
            ["user_id", "session_id", "slot"],
        )
        batch_op.create_index("ix_working_expires", ["expires_at"])

    # ── Semantic memories ──────────────────────────────────────────
    op.create_table(
        "semantic_memories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("source", sa.String(200), nullable=True),
        sa.Column("access_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_accessed", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("semantic_memories", schema=None) as batch_op:
        batch_op.create_index("ix_semantic_user_category", ["user_id", "category"])
        batch_op.create_index("ix_semantic_user_confidence", ["user_id", "confidence"])
        batch_op.create_index("ix_semantic_memories_user_id", ["user_id"])
        batch_op.create_index("ix_semantic_memories_category", ["category"])

    # ── Memory graph nodes ─────────────────────────────────────────
    op.create_table(
        "memory_nodes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("memory_type", sa.String(50), nullable=False),
        sa.Column("memory_id", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(200), nullable=False),
        sa.Column("embedding_id", sa.String(100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id", "memory_type", "memory_id", name="uq_memory_node_target"
        ),
    )
    with op.batch_alter_table("memory_nodes", schema=None) as batch_op:
        batch_op.create_index("ix_memory_nodes_user_id", ["user_id"])
        batch_op.create_index("ix_memory_node_user_type", ["user_id", "memory_type"])

    # ── Memory graph edges ─────────────────────────────────────────
    op.create_table(
        "memory_edges",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "source_id",
            sa.Integer(),
            sa.ForeignKey("memory_nodes.id"),
            nullable=False,
        ),
        sa.Column(
            "target_id",
            sa.Integer(),
            sa.ForeignKey("memory_nodes.id"),
            nullable=False,
        ),
        sa.Column("edge_type", sa.String(100), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_id", "target_id", "edge_type", name="uq_memory_edge"
        ),
    )
    with op.batch_alter_table("memory_edges", schema=None) as batch_op:
        batch_op.create_index("ix_memory_edges_source_id", ["source_id"])
        batch_op.create_index("ix_memory_edges_target_id", ["target_id"])
        batch_op.create_index("ix_memory_edges_weight", ["weight"])


def downgrade() -> None:
    # Drop memory tables (reverse order for FK constraints)
    op.drop_table("memory_edges")
    op.drop_table("memory_nodes")
    op.drop_table("semantic_memories")
    op.drop_table("working_memories")
    op.drop_table("episodic_memories")

    # Revert system_snapshots column types
    with op.batch_alter_table("system_snapshots", schema=None) as batch_op:
        batch_op.alter_column(
            "network_recv_bytes",
            existing_type=sa.BigInteger(),
            type_=sa.Integer(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "network_sent_bytes",
            existing_type=sa.BigInteger(),
            type_=sa.Integer(),
            existing_nullable=False,
        )
