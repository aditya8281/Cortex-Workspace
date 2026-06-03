"""create_model_routing_tables

Revision ID: 7b5626346da3
Revises: de66352532a7
Create Date: 2026-06-03 22:23:57.927905

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b5626346da3'
down_revision: Union[str, Sequence[str], None] = 'de66352532a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'cortex_routing_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=64), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cortex_routing_profiles_id'), 'cortex_routing_profiles', ['id'], unique=False)
    op.create_index(op.f('ix_cortex_routing_profiles_name'), 'cortex_routing_profiles', ['name'], unique=True)

    op.create_table(
        'cortex_task_routes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('profile_name', sa.String(length=64), nullable=False),
        sa.Column('task_type', sa.String(length=64), nullable=False),
        sa.Column('primary_model', sa.String(length=256), nullable=False),
        sa.Column('fallback_model', sa.String(length=256), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cortex_task_routes_id'), 'cortex_task_routes', ['id'], unique=False)
    op.create_index(op.f('ix_cortex_task_routes_profile_name'), 'cortex_task_routes', ['profile_name'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_cortex_task_routes_profile_name'), table_name='cortex_task_routes')
    op.drop_index(op.f('ix_cortex_task_routes_id'), table_name='cortex_task_routes')
    op.drop_table('cortex_task_routes')
    op.drop_index(op.f('ix_cortex_routing_profiles_name'), table_name='cortex_routing_profiles')
    op.drop_index(op.f('ix_cortex_routing_profiles_id'), table_name='cortex_routing_profiles')
    op.drop_table('cortex_routing_profiles')
