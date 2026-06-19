"""Add developer profile fields to users.

Revision ID: l00000000012
Revises: k00000000011
Create Date: 2026-06-19 21:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "l00000000012"
down_revision: str | None = "k00000000011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("programming_languages", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("users", sa.Column("frameworks", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("users", sa.Column("current_projects", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("users", sa.Column("contribution_style", sa.String(32), nullable=True))
    op.add_column("users", sa.Column("social_links", sa.JSON(), nullable=False, server_default="{}"))


def downgrade() -> None:
    op.drop_column("users", "social_links")
    op.drop_column("users", "contribution_style")
    op.drop_column("users", "current_projects")
    op.drop_column("users", "frameworks")
    op.drop_column("users", "programming_languages")
