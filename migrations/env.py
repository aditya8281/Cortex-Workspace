"""Alembic environment configuration.

Resolves the database URL from application settings (DATABASE_URL).
"""

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Alembic Config object — provides access to values in the .ini file.
config = context.config

# Set up loggers from the config file.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Resolve the database URL from environment / .env.
# This ensures CLI `alembic` commands and the running app always target
# the same database, regardless of CWD.
_db_url = os.environ.get("DATABASE_URL", "")
if not _db_url:
    # Fall back to settings (reads .env automatically)
    try:
        from backend.app.core.config import settings

        _db_url = settings.DATABASE_URL
    except Exception:
        pass

if _db_url:
    # Alembic uses sync connections — strip async driver for sync fallback
    _sync_url = _db_url.replace("+asyncpg", "+psycopg2")
    config.set_main_option("sqlalchemy.url", _sync_url)

# Import models so Alembic autogenerate can detect them.
from backend.app.db.base import Base  # noqa: E402
from backend.app.intelligence.models import KnowledgeEntry  # noqa: F401, E402
from backend.app.models.awareness.file_index import IndexedFile  # noqa: F401, E402
from backend.app.models.awareness.indexing_config import IndexingConfig  # noqa: F401, E402
from backend.app.models.awareness.repo_index import CodeChunk, RepoIndex  # noqa: F401, E402
from backend.app.models.cognition.agent import Agent, AgentFeedback, AgentRun, AgentStep  # noqa: F401, E402
from backend.app.models.integration.sync_state import SyncState  # noqa: F401, E402
from backend.app.models.intelligence.embedding_cache import EmbeddingCache  # noqa: F401, E402
from backend.app.models.intelligence.model_catalog import (  # noqa: F401, E402
    Capability,
    HardwareProfile,
    ModelCatalog,
    ModelDownload,
    ModelStatistics,
    ModelUsage,
    ModelVariant,
    Provider,
    ProviderModel,
    Quantization,
    SyncJob,
)
from backend.app.models.interaction.conversation import Conversation, ConversationMessage  # noqa: F401, E402
from backend.app.models.interaction.notification import Notification  # noqa: F401, E402
from backend.app.models.interaction.user import User  # noqa: F401, E402
from backend.app.models.awareness.system_snapshot import SystemSnapshot  # noqa: F401, E402
from backend.app.models.memory.document import Document, DocumentChunk  # noqa: F401, E402
from backend.app.models.memory.episodic import EpisodicMemory  # noqa: F401, E402
from backend.app.models.memory.graph import GraphEdge, GraphNode  # noqa: F401, E402
from backend.app.models.memory.long_term_memory import LongTermMemory  # noqa: F401, E402
from backend.app.models.memory.memory_graph import MemoryEdge, MemoryNode  # noqa: F401, E402
from backend.app.models.memory.path_index import PathIndex  # noqa: F401, E402
from backend.app.models.memory.semantic import SemanticMemory  # noqa: F401, E402
from backend.app.models.memory.storage_registry import StorageRegistry  # noqa: F401, E402
from backend.app.models.memory.working import WorkingMemory  # noqa: F401, E402
from backend.app.models.privacy.auth_event import AuthEvent  # noqa: F401, E402
from backend.app.models.privacy.user_settings import UserModelSettings  # noqa: F401, E402
from backend.app.models.system.agent_run_event import AgentRunEvent, AgentRunToolCall  # noqa: F401, E402
from backend.app.models.system.mcp_server import MCPServer, MCPServerTool  # noqa: F401, E402
from backend.app.models.system.observability import (  # noqa: F401, E402
    PerformanceBaseline,
    TokenUsage,
    ToolExecutionMetrics,
)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode — emits SQL without connecting."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode — connects to the live database."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
