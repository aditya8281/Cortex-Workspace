"""add role field to users

Revision ID: 3a5b9f32d36d
Revises: e4834d8614aa
Create Date: 2026-06-02 04:00:05.550696

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3a5b9f32d36d'
down_revision: Union[str, Sequence[str], None] = 'e4834d8614aa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('role', sa.String(), server_default='user', nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'role')
