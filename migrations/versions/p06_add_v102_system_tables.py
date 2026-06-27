"""Add v1.02 system tables — MCP server registry, agent run events, observability.

Revision ID: p06_add_v102_system_tables
Revises: 6226c3a2cb5e
Create Date: 2026-06-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "p06_add_v102_system_tables"
down_revision: str | Sequence[str] | None = "6226c3a2cb5e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── MCP Servers ──────────────────────────────────────────────────
    op.create_table(
        "mcp_servers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("command", sa.String(500), nullable=True),
        sa.Column("args", postgresql.JSONB(), nullable=True),
        sa.Column("env", postgresql.JSONB(), nullable=True),
        sa.Column("transport", sa.String(50), nullable=False, server_default="stdio"),
        sa.Column("sse_url", sa.String(1000), nullable=True),
        sa.Column("working_dir", sa.String(1000), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("health_check_interval", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("max_restarts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_mcp_servers_name", "mcp_servers", ["name"], unique=True)
    op.create_index("ix_mcp_servers_user_id", "mcp_servers", ["user_id"])
    op.create_index("ix_mcp_servers_enabled", "mcp_servers", ["enabled"])

    # ── MCP Server Tools ─────────────────────────────────────────────
    op.create_table(
        "mcp_server_tools",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "server_id",
            sa.Integer(),
            sa.ForeignKey("mcp_servers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tool_name", sa.String(255), nullable=False),
        sa.Column("tool_description", sa.Text(), nullable=True),
        sa.Column("tool_schema", postgresql.JSONB(), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_mcp_server_tools_server_id", "mcp_server_tools", ["server_id"])
    op.create_index(
        "ix_mcp_server_tools_unique",
        "mcp_server_tools",
        ["server_id", "tool_name"],
        unique=True,
    )

    # ── Agent Run Events (replay buffer) ─────────────────────────────
    op.create_table(
        "agent_run_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "run_id",
            sa.Integer(),
            sa.ForeignKey("agent_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("event_data", postgresql.JSONB(), nullable=False),
        sa.Column("sequence_num", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_agent_run_events_run_id", "agent_run_events", ["run_id"])
    op.create_index(
        "ix_agent_run_events_sequence",
        "agent_run_events",
        ["run_id", "sequence_num"],
    )

    # ── Agent Run Tool Calls ─────────────────────────────────────────
    op.create_table(
        "agent_run_tool_calls",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "run_id",
            sa.Integer(),
            sa.ForeignKey("agent_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tool_name", sa.String(255), nullable=False),
        sa.Column("tool_args", postgresql.JSONB(), nullable=True),
        sa.Column("tool_result", sa.Text(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("duration_ms", sa.Float(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_agent_run_tool_calls_run_id", "agent_run_tool_calls", ["run_id"])
    op.create_index("ix_agent_run_tool_calls_tool_name", "agent_run_tool_calls", ["tool_name"])

    # ── Token Usage ──────────────────────────────────────────────────
    op.create_table(
        "token_usage",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("run_id", sa.String(36), nullable=True),
        sa.Column("model", sa.String(255), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("total_tokens", sa.Integer(), nullable=False),
        sa.Column("context_window", sa.Integer(), nullable=True),
        sa.Column("context_usage_pct", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_token_usage_user_id", "token_usage", ["user_id"])
    op.create_index("ix_token_usage_created_at", "token_usage", ["created_at"])
    op.create_index("ix_token_usage_model", "token_usage", ["model"])
    op.create_index("ix_token_usage_user_date", "token_usage", ["user_id", "created_at"])

    # ── Tool Execution Metrics ───────────────────────────────────────
    op.create_table(
        "tool_execution_metrics",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tool_name", sa.String(255), nullable=False),
        sa.Column("is_mcp", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("mcp_server", sa.String(255), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("duration_ms", sa.Float(), nullable=False),
        sa.Column("output_size_bytes", sa.Integer(), nullable=True),
        sa.Column("error_type", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_tool_exec_metrics_tool_name", "tool_execution_metrics", ["tool_name"])
    op.create_index("ix_tool_exec_metrics_created_at", "tool_execution_metrics", ["created_at"])
    op.create_index("ix_tool_metrics_tool_date", "tool_execution_metrics", ["tool_name", "created_at"])

    # ── Performance Baselines ────────────────────────────────────────
    op.create_table(
        "performance_baselines",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("metric_name", sa.String(255), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=False),
        sa.Column("metric_unit", sa.String(50), nullable=True),
        sa.Column("context", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_perf_baselines_metric_name", "performance_baselines", ["metric_name"])


def downgrade() -> None:
    op.drop_table("performance_baselines")
    op.drop_table("tool_execution_metrics")
    op.drop_table("token_usage")
    op.drop_table("agent_run_tool_calls")
    op.drop_table("agent_run_events")
    op.drop_table("mcp_server_tools")
    op.drop_table("mcp_servers")
