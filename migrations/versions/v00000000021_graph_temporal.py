"""Add temporal tracking to graph_edges.

Revision ID: v00000000021
Revises: u00000000020
Create Date: 2026-06-21
"""

from alembic import op
import sqlalchemy as sa

revision = "v00000000021"
down_revision = "u00000000020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "graph_edges",
        sa.Column(
            "first_seen", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
    )
    op.add_column(
        "graph_edges",
        sa.Column(
            "last_seen", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
    )


def downgrade() -> None:
    op.drop_column("graph_edges", "last_seen")
    op.drop_column("graph_edges", "first_seen")
