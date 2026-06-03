"""add user profiles table

Revision ID: d4e8f1a2c3b0
Revises: c8f21a2b9e10
Create Date: 2026-06-03 20:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e8f1a2c3b0"
down_revision: Union[str, Sequence[str], None] = "c8f21a2b9e10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("display_name", sa.String(256), nullable=True),
        sa.Column("job_title", sa.String(256), nullable=True),
        sa.Column("location", sa.String(256), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("interests_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("goals_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("focus_areas_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("languages_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("onboarding_completed", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_user_profiles_user_id", "user_profiles", ["user_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_user_profiles_user_id", table_name="user_profiles")
    op.drop_table("user_profiles")
