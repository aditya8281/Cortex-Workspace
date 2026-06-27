"""add pid and state_snapshot to agent_runs

Revision ID: 6226c3a2cb5e
Revises: c00000000005
Create Date: 2026-06-25 16:02:43.199649

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '6226c3a2cb5e'
down_revision: str | Sequence[str] | None = 'c00000000005'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add pid and state_snapshot columns to agent_runs."""
    op.add_column("agent_runs", sa.Column("pid", sa.Integer(), nullable=True, index=True))
    op.add_column("agent_runs", sa.Column("state_snapshot", sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove pid and state_snapshot columns from agent_runs."""
    op.drop_column("agent_runs", "state_snapshot")
    op.drop_column("agent_runs", "pid")
