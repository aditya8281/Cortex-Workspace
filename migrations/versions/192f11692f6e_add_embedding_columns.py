"""add_embedding_columns

Revision ID: 192f11692f6e
Revises: 9e05362652b9
Create Date: 2026-06-30 11:02:46.186256

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '192f11692f6e'
down_revision: Union[str, Sequence[str], None] = '9e05362652b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("model_catalog", sa.Column("embedding_dim", sa.Integer(), nullable=True))
    op.add_column("model_catalog", sa.Column("pooling_type", sa.String(20), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("model_catalog", "pooling_type")
    op.drop_column("model_catalog", "embedding_dim")
