"""Set username NOT NULL

Revision ID: a0b1c2d3e4f5
Revises: f1a2b3c4d5e6
Create Date: 2026-06-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a0b1c2d3e4f5'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Fill any NULL usernames with a fallback based on id
    conn = op.get_bind()
    try:
        conn.execute(sa.text("UPDATE users SET username = 'user' || id WHERE username IS NULL"))
    except Exception:
        # best-effort: different DBs may require different concat operators; ignore if fails
        pass

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('username', existing_type=sa.String(), nullable=False)


def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('username', existing_type=sa.String(), nullable=True)
