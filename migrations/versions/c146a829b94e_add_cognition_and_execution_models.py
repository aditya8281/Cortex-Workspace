"""add cognition and execution models

Revision ID: c146a829b94e
Revises: a1b2c3d4e5f6
Create Date: 2026-06-28 20:14:42.895272

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c146a829b94e'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create cognition and execution domain tables."""
    # --- Cognition domain ---

    op.create_table(
        'task_plans',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('goal', sa.Text(), nullable=False),
        sa.Column('steps', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('current_step', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('estimated_duration_ms', sa.Integer(), nullable=True),
        sa.Column('actual_duration_ms', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_task_plans_user_id', 'task_plans', ['user_id'], unique=False)
    op.create_index('ix_task_plan_user_status', 'task_plans', ['user_id', 'status'], unique=False)
    op.create_index('ix_task_plan_user_created', 'task_plans', ['user_id', 'created_at'], unique=False)

    op.create_table(
        'error_analyses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('error_type', sa.String(length=100), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('fingerprint', sa.String(length=200), nullable=True),
        sa.Column('context', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('root_cause', sa.Text(), nullable=True),
        sa.Column('resolution', sa.Text(), nullable=True),
        sa.Column('prevention', sa.Text(), nullable=True),
        sa.Column('severity', sa.String(length=20), nullable=False, server_default='info'),
        sa.Column('resolved', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('resolution_method', sa.String(length=50), nullable=True),
        sa.Column('related_analysis_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_error_analyses_user_id', 'error_analyses', ['user_id'], unique=False)
    op.create_index('ix_error_user_type', 'error_analyses', ['user_id', 'error_type'], unique=False)
    op.create_index('ix_error_analyses_fingerprint', 'error_analyses', ['fingerprint'], unique=False)

    op.create_table(
        'hypotheses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('hypothesis', sa.Text(), nullable=False),
        sa.Column('evidence_for', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('evidence_against', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('confidence_history', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('related_plan_id', sa.Integer(), nullable=True),
        sa.Column('related_hypothesis_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolution_reason', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_hypotheses_user_id', 'hypotheses', ['user_id'], unique=False)
    op.create_index('ix_hypothesis_user_status', 'hypotheses', ['user_id', 'status'], unique=False)
    op.create_index('ix_hypothesis_user_confidence', 'hypotheses', ['user_id', 'confidence'], unique=False)

    op.create_table(
        'confidence_scores',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('task_type', sa.String(length=100), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('factors', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('context', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('actual_outcome', sa.String(length=50), nullable=True),
        sa.Column('was_accurate', sa.Integer(), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('related_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_confidence_scores_user_id', 'confidence_scores', ['user_id'], unique=False)
    op.create_index('ix_confidence_user_task', 'confidence_scores', ['user_id', 'task_type'], unique=False)

    # --- Execution domain ---

    op.create_table(
        'tool_executions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('tool_name', sa.String(length=100), nullable=False),
        sa.Column('parameters', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('result', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_type', sa.String(length=100), nullable=True),
        sa.Column('verification_result', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('parent_execution_id', sa.Integer(), nullable=True),
        sa.Column('workflow_id', sa.Integer(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_tool_executions_user_id', 'tool_executions', ['user_id'], unique=False)
    op.create_index('ix_tool_exec_user_tool', 'tool_executions', ['user_id', 'tool_name'], unique=False)
    op.create_index('ix_tool_executions_status', 'tool_executions', ['status'], unique=False)
    op.create_index('ix_tool_executions_workflow_id', 'tool_executions', ['workflow_id'], unique=False)

    op.create_table(
        'workflows',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('steps', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='idle'),
        sa.Column('current_step', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_run', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_run_status', sa.String(length=50), nullable=True),
        sa.Column('run_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_duration_ms', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_workflows_user_id', 'workflows', ['user_id'], unique=False)
    op.create_index('ix_workflow_user_status', 'workflows', ['user_id', 'status'], unique=False)
    op.create_index('ix_workflow_user_created', 'workflows', ['user_id', 'created_at'], unique=False)


def downgrade() -> None:
    """Drop cognition and execution domain tables."""
    op.drop_index('ix_workflow_user_created', table_name='workflows')
    op.drop_index('ix_workflow_user_status', table_name='workflows')
    op.drop_index('ix_workflows_user_id', table_name='workflows')
    op.drop_table('workflows')

    op.drop_index('ix_tool_executions_workflow_id', table_name='tool_executions')
    op.drop_index('ix_tool_executions_status', table_name='tool_executions')
    op.drop_index('ix_tool_exec_user_tool', table_name='tool_executions')
    op.drop_index('ix_tool_executions_user_id', table_name='tool_executions')
    op.drop_table('tool_executions')

    op.drop_index('ix_confidence_user_task', table_name='confidence_scores')
    op.drop_index('ix_confidence_scores_user_id', table_name='confidence_scores')
    op.drop_table('confidence_scores')

    op.drop_index('ix_hypothesis_user_confidence', table_name='hypotheses')
    op.drop_index('ix_hypothesis_user_status', table_name='hypotheses')
    op.drop_index('ix_hypotheses_user_id', table_name='hypotheses')
    op.drop_table('hypotheses')

    op.drop_index('ix_error_analyses_fingerprint', table_name='error_analyses')
    op.drop_index('ix_error_user_type', table_name='error_analyses')
    op.drop_index('ix_error_analyses_user_id', table_name='error_analyses')
    op.drop_table('error_analyses')

    op.drop_index('ix_task_plan_user_created', table_name='task_plans')
    op.drop_index('ix_task_plan_user_status', table_name='task_plans')
    op.drop_index('ix_task_plans_user_id', table_name='task_plans')
    op.drop_table('task_plans')
