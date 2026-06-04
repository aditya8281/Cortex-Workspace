"""add provider default model name

Revision ID: 9b7f6f0f8e21
Revises: 48a574a20409
Create Date: 2026-06-04 12:55:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9b7f6f0f8e21"
down_revision: Union[str, Sequence[str], None] = "48a574a20409"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("cortex_providers", sa.Column("default_model_name", sa.String(length=256), nullable=True))


def downgrade() -> None:
    op.drop_column("cortex_providers", "default_model_name")
