"""Add Ollama model registry tables

Revision ID: g2h3i4j5k6l7
Revises: f1a2b3c4d5e6
Create Date: 2025-06-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'g2h3i4j5k6l7'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ollama_registry_models table
    op.create_table(
        'ollama_registry_models',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('model_id', sa.String(128), nullable=False, unique=True),
        sa.Column('family', sa.String(64), nullable=False),
        sa.Column('display_name', sa.String(256), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tags', sa.Text(), nullable=True),
        sa.Column('capabilities', sa.Text(), nullable=True),
        sa.Column('parameters', sa.String(64), nullable=True),
        sa.Column('context_length', sa.Integer(), nullable=True),
        sa.Column('quantization', sa.String(64), nullable=False, server_default='unknown'),
        sa.Column('source_url', sa.String(512), nullable=False),
        sa.Column('pull_command', sa.String(256), nullable=False),
        sa.Column('is_installed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('last_installed_at', sa.DateTime(), nullable=True),
        sa.Column('last_synced_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ollama_registry_models_model_id'), 'ollama_registry_models', ['model_id'], unique=True)
    op.create_index(op.f('ix_ollama_registry_models_family'), 'ollama_registry_models', ['family'])
    op.create_index(op.f('ix_ollama_registry_models_is_installed'), 'ollama_registry_models', ['is_installed'])

    # Create ollama_download_progress table
    op.create_table(
        'ollama_download_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('model_id', sa.String(128), nullable=False),
        sa.Column('status', sa.String(32), nullable=False, server_default='queued'),
        sa.Column('progress_percent', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('bytes_downloaded', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_bytes', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ollama_download_progress_model_id'), 'ollama_download_progress', ['model_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_ollama_download_progress_model_id'), table_name='ollama_download_progress')
    op.drop_table('ollama_download_progress')
    op.drop_index(op.f('ix_ollama_registry_models_is_installed'), table_name='ollama_registry_models')
    op.drop_index(op.f('ix_ollama_registry_models_family'), table_name='ollama_registry_models')
    op.drop_index(op.f('ix_ollama_registry_models_model_id'), table_name='ollama_registry_models')
    op.drop_table('ollama_registry_models')
