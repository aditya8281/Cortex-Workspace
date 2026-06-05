"""Merge remaining heads: 7c6b5a4d3e2f and a0b1c2d3e4f5

Revision ID: b1c2d3e4f6a7
Revises: 7c6b5a4d3e2f, a0b1c2d3e4f5
Create Date: 2026-06-05 00:00:00.000000
"""

from __future__ import annotations

from alembic import op  # noqa: F401


# revision identifiers, used by Alembic.
revision = "b1c2d3e4f6a7"
down_revision = ("7c6b5a4d3e2f", "a0b1c2d3e4f5")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # merge revision: no schema changes
    pass


def downgrade() -> None:
    pass
