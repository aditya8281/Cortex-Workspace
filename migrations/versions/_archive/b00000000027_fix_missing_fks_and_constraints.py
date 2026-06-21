"""Fix missing foreign keys, add CHECK constraints, indexes, and defaults.

Revision ID: b00000000027
Revises: z00000000025
Create Date: 2026-06-22
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b00000000027"
down_revision: str | None = "z00000000025"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _safe_execute(sql: str) -> None:
    """Execute SQL, ignoring errors for idempotent operations."""
    try:
        op.execute(sql)
    except Exception:
        pass


def upgrade() -> None:
    # ── 1. Add missing foreign keys ─────────────────────────────

    # conversations.user_id → users.id (CASCADE)
    _safe_execute(
        "ALTER TABLE conversations "
        "ADD CONSTRAINT fk_conversations_user_id "
        "FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE"
    )

    # conversations.repo_id → repo_indexes.id (SET NULL)
    _safe_execute(
        "ALTER TABLE conversations "
        "ADD CONSTRAINT fk_conversations_repo_id "
        "FOREIGN KEY (repo_id) REFERENCES repo_indexes(id) ON DELETE SET NULL"
    )

    # long_term_memories.user_id → users.id (CASCADE)
    _safe_execute(
        "ALTER TABLE long_term_memories "
        "ADD CONSTRAINT fk_ltm_user_id "
        "FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE"
    )

    # sync_states.user_id → users.id (CASCADE)
    _safe_execute(
        "ALTER TABLE sync_states "
        "ADD CONSTRAINT fk_sync_states_user_id "
        "FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE"
    )

    # sync_states.repo_id → repo_indexes.id (SET NULL)
    _safe_execute(
        "ALTER TABLE sync_states "
        "ADD CONSTRAINT fk_sync_states_repo_id "
        "FOREIGN KEY (repo_id) REFERENCES repo_indexes(id) ON DELETE SET NULL"
    )

    # agents: add user_id column + FK to users.id (CASCADE)
    _safe_execute(
        "ALTER TABLE agents "
        "ADD COLUMN user_id INTEGER"
    )
    _safe_execute(
        "ALTER TABLE agents "
        "ADD CONSTRAINT fk_agents_user_id "
        "FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE"
    )
    _safe_execute("CREATE INDEX IF NOT EXISTS ix_agents_user_id ON agents (user_id)")

    # ── 2. Add CHECK constraints ────────────────────────────────

    # users.role IN ('user', 'admin')
    _safe_execute(
        "ALTER TABLE users "
        "ADD CONSTRAINT ck_users_role CHECK (role IN ('user', 'admin'))"
    )

    # conversation_messages.role IN ('system', 'user', 'assistant')
    _safe_execute(
        "ALTER TABLE conversation_messages "
        "ADD CONSTRAINT ck_conv_msg_role CHECK (role IN ('system', 'user', 'assistant'))"
    )

    # ── 3. Add indexes for frequently queried columns ───────────

    _safe_execute(
        "CREATE INDEX IF NOT EXISTS idx_conversations_user_updated "
        "ON conversations (user_id, updated_at)"
    )
    _safe_execute(
        "CREATE INDEX IF NOT EXISTS idx_ltm_user_category "
        "ON long_term_memories (user_id, category)"
    )
    _safe_execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_sync_states_user_repo "
        "ON sync_states (user_id, repo_path)"
    )
    _safe_execute(
        "CREATE INDEX IF NOT EXISTS idx_agent_feedback_user "
        "ON agent_feedback (user_id)"
    )
    _safe_execute(
        "CREATE INDEX IF NOT EXISTS idx_model_downloads_user_status "
        "ON model_downloads (user_id, status)"
    )

    # ── 4. Fix nullability defaults on indexed_files ────────────

    _safe_execute(
        "ALTER TABLE indexed_files "
        "ALTER COLUMN file_size SET DEFAULT 0"
    )
    _safe_execute(
        "ALTER TABLE indexed_files "
        "ALTER COLUMN mtime SET DEFAULT 0"
    )


def downgrade() -> None:
    # ── 4. Revert indexed_files defaults ────────────────────────
    _safe_execute(
        "ALTER TABLE indexed_files ALTER COLUMN file_size DROP DEFAULT"
    )
    _safe_execute(
        "ALTER TABLE indexed_files ALTER COLUMN mtime DROP DEFAULT"
    )

    # ── 3. Drop indexes ─────────────────────────────────────────
    _safe_execute("DROP INDEX IF EXISTS idx_model_downloads_user_status")
    _safe_execute("DROP INDEX IF EXISTS idx_agent_feedback_user")
    _safe_execute("DROP INDEX IF EXISTS idx_sync_states_user_repo")
    _safe_execute("DROP INDEX IF EXISTS idx_ltm_user_category")
    _safe_execute("DROP INDEX IF EXISTS idx_conversations_user_updated")

    # ── 2. Drop CHECK constraints ───────────────────────────────
    _safe_execute("ALTER TABLE conversation_messages DROP CONSTRAINT IF EXISTS ck_conv_msg_role")
    _safe_execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS ck_users_role")

    # ── 1. Drop foreign keys and agents.user_id ─────────────────
    _safe_execute("DROP INDEX IF EXISTS ix_agents_user_id")
    _safe_execute("ALTER TABLE agents DROP CONSTRAINT IF EXISTS fk_agents_user_id")
    _safe_execute("ALTER TABLE agents DROP COLUMN IF EXISTS user_id")

    _safe_execute("ALTER TABLE sync_states DROP CONSTRAINT IF EXISTS fk_sync_states_repo_id")
    _safe_execute("ALTER TABLE sync_states DROP CONSTRAINT IF EXISTS fk_sync_states_user_id")
    _safe_execute("ALTER TABLE long_term_memories DROP CONSTRAINT IF EXISTS fk_ltm_user_id")
    _safe_execute("ALTER TABLE conversations DROP CONSTRAINT IF EXISTS fk_conversations_repo_id")
    _safe_execute("ALTER TABLE conversations DROP CONSTRAINT IF EXISTS fk_conversations_user_id")
