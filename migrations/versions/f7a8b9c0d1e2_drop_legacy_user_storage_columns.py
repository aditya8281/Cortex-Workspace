"""Drop legacy user storage columns.

The canonical storage root is now exclusively in the ``user_storage_registry`` table.
Columns ``data_path`` and ``personal_storage_path`` on the ``users`` table have been
removed from both the ORM model and the physical schema.

Revision ID: f7a8b9c0d1e2
Revises: d1e2f3a4b5c6
Create Date: 2026-06-07
"""

from alembic import op
import sqlalchemy as sa

revision = "f7a8b9c0d1e2"
down_revision = "d1e2f3a4b5c6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("data_path")
        batch_op.drop_column("personal_storage_path")


def downgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("data_path", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("personal_storage_path", sa.String(), nullable=True))
