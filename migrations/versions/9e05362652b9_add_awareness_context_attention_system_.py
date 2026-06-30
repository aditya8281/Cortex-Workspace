"""add awareness context attention system_snapshot tables

Revision ID: 9e05362652b9
Revises: c146a829b94e
Create Date: 2026-06-30 00:23:46.211893

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '9e05362652b9'
down_revision: str | Sequence[str] | None = 'c146a829b94e'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create awareness context, attention, and system snapshot tables."""

    # --- system_snapshots ---
    op.create_table('system_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('cpu_percent', sa.Float(), nullable=False),
        sa.Column('memory_percent', sa.Float(), nullable=False),
        sa.Column('memory_used_gb', sa.Float(), nullable=False),
        sa.Column('memory_total_gb', sa.Float(), nullable=False),
        sa.Column('disk_percent', sa.Float(), nullable=False),
        sa.Column('disk_used_gb', sa.Float(), nullable=False),
        sa.Column('disk_total_gb', sa.Float(), nullable=False),
        sa.Column('gpu_percent', sa.Float(), nullable=True),
        sa.Column('gpu_memory_used_gb', sa.Float(), nullable=True),
        sa.Column('gpu_memory_total_gb', sa.Float(), nullable=True),
        sa.Column('network_sent_bytes', sa.Integer(), nullable=False),
        sa.Column('network_recv_bytes', sa.Integer(), nullable=False),
        sa.Column('load_average_1m', sa.Float(), nullable=True),
        sa.Column('load_average_5m', sa.Float(), nullable=True),
        sa.Column('load_average_15m', sa.Float(), nullable=True),
        sa.Column('process_count', sa.Integer(), nullable=False),
        sa.Column('uptime_seconds', sa.Float(), nullable=False),
        sa.Column('meta', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_system_snapshots_user_id', 'system_snapshots', ['user_id'])

    # --- attention_tracker ---
    op.create_table('attention_tracker',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('session_type', sa.String(length=32), nullable=False),
        sa.Column('task_description', sa.String(length=512), nullable=True),
        sa.Column('focus_score', sa.Float(), nullable=False),
        sa.Column('distraction_count', sa.Integer(), nullable=False),
        sa.Column('switch_count', sa.Integer(), nullable=False),
        sa.Column('duration_seconds', sa.Float(), nullable=False),
        sa.Column('productive_seconds', sa.Float(), nullable=False),
        sa.Column('active_apps', sa.JSON(), nullable=False),
        sa.Column('context_switches', sa.JSON(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_attention_tracker_user_id', 'attention_tracker', ['user_id'])

    # --- context_rules ---
    op.create_table('context_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=512), nullable=True),
        sa.Column('rule_type', sa.String(length=32), nullable=False),
        sa.Column('conditions', sa.JSON(), nullable=False),
        sa.Column('actions', sa.JSON(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('enabled', sa.Integer(), nullable=False),
        sa.Column('hit_count', sa.Integer(), nullable=False),
        sa.Column('last_hit_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_context_rules_user_id', 'context_rules', ['user_id'])

    # --- context_states ---
    op.create_table('context_states',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('state_key', sa.String(length=128), nullable=False),
        sa.Column('state_value', sa.JSON(), nullable=False),
        sa.Column('source', sa.String(length=64), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'state_key', name='uq_context_states_user_key')
    )
    op.create_index('ix_context_states_user_id', 'context_states', ['user_id'])

    # --- context_events ---
    op.create_table('context_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('event_data', sa.JSON(), nullable=False),
        sa.Column('source', sa.String(length=64), nullable=False),
        sa.Column('relevance_score', sa.Float(), nullable=False),
        sa.Column('related_rule_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['related_rule_id'], ['context_rules.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_context_events_user_id', 'context_events', ['user_id'])


def downgrade() -> None:
    """Drop awareness context, attention, and system snapshot tables."""
    op.drop_table('context_events')
    op.drop_table('context_states')
    op.drop_table('context_rules')
    op.drop_table('attention_tracker')
    op.drop_table('system_snapshots')
