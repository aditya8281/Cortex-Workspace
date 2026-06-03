"""add intelligence tables

Revision ID: c8f21a2b9e10
Revises: 3790db00941b
Create Date: 2026-06-03 18:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c8f21a2b9e10"
down_revision: Union[str, Sequence[str], None] = "3790db00941b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sync_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("started_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("files_indexed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("files_added", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("files_modified", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("files_removed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("repositories_indexed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("memory_updates", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("progress_message", sa.String(512), nullable=True),
        sa.Column("result_summary", sa.Text(), nullable=True),
    )
    op.create_index("ix_sync_runs_user_id", "sync_runs", ["user_id"])
    op.create_index("ix_sync_runs_started_at", "sync_runs", ["started_at"])

    op.create_table(
        "knowledge_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source_path", sa.String(1024), nullable=True),
        sa.Column("source_key", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_knowledge_entries_category", "knowledge_entries", ["category"])
    op.create_index("ix_knowledge_entries_source_key", "knowledge_entries", ["source_key"])

    op.create_table(
        "repository_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("path", sa.String(1024), nullable=False, unique=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("architecture_summary", sa.Text(), nullable=False),
        sa.Column("tech_stack", sa.Text(), nullable=False),
        sa.Column("dependencies_json", sa.Text(), nullable=False),
        sa.Column("entry_points_json", sa.Text(), nullable=False),
        sa.Column("important_files_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_repository_profiles_path", "repository_profiles", ["path"], unique=True)

    op.create_table(
        "proactive_notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("priority", sa.String(16), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("action_type", sa.String(64), nullable=True),
        sa.Column("action_payload_json", sa.Text(), nullable=True),
        sa.Column("dismissed", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "pending_system_actions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action_type", sa.String(64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("affected_paths_json", sa.Text(), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "cortex_automation_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("automation_level", sa.String(32), nullable=False),
        sa.Column("trusted_categories_json", sa.Text(), nullable=False),
        sa.Column("observer_enabled", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_cortex_automation_settings_user_id",
        "cortex_automation_settings",
        ["user_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_table("cortex_automation_settings")
    op.drop_table("pending_system_actions")
    op.drop_table("proactive_notifications")
    op.drop_table("repository_profiles")
    op.drop_table("knowledge_entries")
    op.drop_index("ix_sync_runs_started_at", table_name="sync_runs")
    op.drop_index("ix_sync_runs_user_id", table_name="sync_runs")
    op.drop_table("sync_runs")
