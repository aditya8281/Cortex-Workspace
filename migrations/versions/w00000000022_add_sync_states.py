"""Add sync_states table for persisting sync state.

Revision ID: w00000000022
Revises: v00000000021
Create Date: 2026-06-21
"""

from alembic import op
import sqlalchemy as sa

revision = "w00000000022"
down_revision = "v00000000021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sync_states",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("repo_path", sa.String(), nullable=False),
        sa.Column("repo_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(), server_default="active"),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("files_watched", sa.Integer(), server_default="0"),
        sa.Column("files_changed", sa.Integer(), server_default="0"),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("config_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_sync_states_user_id", "sync_states", ["user_id"])
    op.create_index("ix_sync_states_repo_path", "sync_states", ["repo_path"])


def downgrade() -> None:
    op.drop_index("ix_sync_states_repo_path")
    op.drop_index("ix_sync_states_user_id")
    op.drop_table("sync_states")
