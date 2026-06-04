"""Enhance model system architecture - add custom model support and fix provider architecture

Revision ID: f1a2b3c4d5e6
Revises: c9ae46f41379
Create Date: 2025-06-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = 'c9ae46f41379'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add custom model fields and enhance model provider separation"""
    
    # Add new columns to cortex_models for better custom model support
    with op.batch_alter_table('cortex_models', schema=None) as batch_op:
        # Add model_identifier for custom models (how the model is referred to in API calls)
        batch_op.add_column(sa.Column('model_identifier', sa.String(256), nullable=True))
        
        # Add api_endpoint for custom models (override endpoint per model if needed)
        batch_op.add_column(sa.Column('api_endpoint', sa.String(512), nullable=True))
        
        # Add provider_type to distinguish local/cloud/custom more clearly
        batch_op.add_column(sa.Column('provider_type', sa.String(32), nullable=True))
        
        # Add source field for better tracking
        batch_op.add_column(sa.Column('source', sa.String(64), nullable=True))
    
    # Add new columns to cortex_providers for better custom provider support
    with op.batch_alter_table('cortex_providers', schema=None) as batch_op:
        # Add provider_type field
        batch_op.add_column(sa.Column('provider_type', sa.String(32), nullable=True))
        
        # Add headers field for custom API authentication (JSON stored as text)
        batch_op.add_column(sa.Column('headers_json', sa.String(2048), nullable=True))
        
        # Add model fetch function name (for provider to dynamically fetch models)
        batch_op.add_column(sa.Column('model_fetch_endpoint', sa.String(256), nullable=True))


def downgrade() -> None:
    """Remove the new columns"""
    with op.batch_alter_table('cortex_providers', schema=None) as batch_op:
        batch_op.drop_column('model_fetch_endpoint')
        batch_op.drop_column('headers_json')
        batch_op.drop_column('provider_type')
    
    with op.batch_alter_table('cortex_models', schema=None) as batch_op:
        batch_op.drop_column('source')
        batch_op.drop_column('provider_type')
        batch_op.drop_column('api_endpoint')
        batch_op.drop_column('model_identifier')
