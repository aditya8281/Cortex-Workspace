"""Add user_model_settings table for persisting model settings.

Revision ID: x00000000023
Revises: w00000000022
Create Date: 2026-06-21
"""

from alembic import op
import sqlalchemy as sa

revision = "x00000000023"
down_revision = "w00000000022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_model_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("inference_backend", sa.String(50), server_default="auto", nullable=False),
        sa.Column("huggingface_token", sa.String(255), nullable=True),
        sa.Column("auto_download", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("max_concurrent_downloads", sa.Integer(), server_default="2", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_user_model_settings_user_id", "user_model_settings", ["user_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_user_model_settings_user_id")
    op.drop_table("user_model_settings")
