"""Merge auth and model registry migration heads.

Revision ID: 8f9e7d6c5b4a
Revises: 0a1b2c3d4e5f, g2h3i4j5k6l7
Create Date: 2026-06-05 00:00:00.000000
"""

from __future__ import annotations

from alembic import op  # noqa: F401


# revision identifiers, used by Alembic.
revision = "8f9e7d6c5b4a"
down_revision = ("0a1b2c3d4e5f", "g2h3i4j5k6l7")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
