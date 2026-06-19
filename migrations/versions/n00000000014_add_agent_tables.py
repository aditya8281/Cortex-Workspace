"""Add agents, agent_runs, agent_steps, and agent_feedback tables.

Revision ID: n00000000014
Revises: m00000000013
Create Date: 2026-06-20 15:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "n00000000014"
down_revision: str | None = "m00000000013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── agents ──────────────────────────────────────────────────
    op.create_table(
        "agents",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True, index=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("model_id", sa.String(100), nullable=False),
        sa.Column("tools_json", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # ── agent_runs ──────────────────────────────────────────────
    op.create_table(
        "agent_runs",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "agent_id",
            sa.Integer(),
            sa.ForeignKey("agents.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("input_text", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("output", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )
    op.create_index("idx_agent_runs_status", "agent_runs", ["status"])
    op.create_index("idx_agent_runs_user", "agent_runs", ["user_id"])

    # ── agent_steps ─────────────────────────────────────────────
    op.create_table(
        "agent_steps",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "run_id",
            sa.Integer(),
            sa.ForeignKey("agent_runs.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("step_number", sa.Integer(), nullable=False),
        sa.Column("thought", sa.Text(), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("action_input_json", sa.Text(), nullable=True),
        sa.Column("observation", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_agent_steps_run_number", "agent_steps", ["run_id", "step_number"])

    # ── agent_feedback ──────────────────────────────────────────
    op.create_table(
        "agent_feedback",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "run_id",
            sa.Integer(),
            sa.ForeignKey("agent_runs.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("agent_feedback")
    op.drop_table("agent_steps")
    op.drop_table("agent_runs")
    op.drop_table("agents")
