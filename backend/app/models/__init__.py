"""Backend domain models — re-exports from domain locations."""

# Memory domain
# Awareness domain
from backend.app.models.awareness.file_index import IndexedFile
from backend.app.models.awareness.indexing_config import IndexingConfig
from backend.app.models.awareness.repo_index import CodeChunk, RepoIndex

# Cognition domain
from backend.app.models.cognition.agent import Agent, AgentFeedback, AgentRun, AgentStep

# Integration domain
from backend.app.models.integration.sync_state import SyncState

# Intelligence domain
from backend.app.models.intelligence.embedding_cache import EmbeddingCache
from backend.app.models.intelligence.model_catalog import (
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

# Interaction domain
from backend.app.models.interaction.conversation import Conversation, ConversationMessage
from backend.app.models.interaction.notification import Notification
from backend.app.models.interaction.user import User
from backend.app.models.memory.document import Document, DocumentChunk, DocumentType
from backend.app.models.memory.graph import GraphEdge, GraphNode
from backend.app.models.memory.long_term_memory import LongTermMemory
from backend.app.models.memory.path_index import PathIndex
from backend.app.models.memory.storage_registry import StorageRegistry

# Privacy domain
from backend.app.models.privacy.auth_event import AuthEvent
from backend.app.models.privacy.user_settings import UserModelSettings

__all__ = [
    # Memory
    "Document",
    "DocumentChunk",
    "DocumentType",
    "GraphEdge",
    "GraphNode",
    "LongTermMemory",
    "PathIndex",
    "StorageRegistry",
    # Awareness
    "IndexedFile",
    "IndexingConfig",
    "CodeChunk",
    "RepoIndex",
    # Intelligence
    "EmbeddingCache",
    "Capability",
    "HardwareProfile",
    "ModelCatalog",
    "ModelDownload",
    "ModelStatistics",
    "ModelUsage",
    "ModelVariant",
    "Provider",
    "ProviderModel",
    "Quantization",
    "SyncJob",
    # Interaction
    "Conversation",
    "ConversationMessage",
    "Notification",
    "User",
    # Cognition
    "Agent",
    "AgentFeedback",
    "AgentRun",
    "AgentStep",
    # Privacy
    "AuthEvent",
    "UserModelSettings",
    # Integration
    "SyncState",
]
