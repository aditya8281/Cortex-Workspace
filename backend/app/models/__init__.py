"""Backend domain models — re-exports from domain locations."""

# Memory domain
# Awareness domain
from backend.app.models.awareness.attention_tracker import AttentionTracker
from backend.app.models.awareness.context_engine import ContextEvent, ContextRule, ContextState
from backend.app.models.awareness.file_index import IndexedFile
from backend.app.models.awareness.indexing_config import IndexingConfig
from backend.app.models.awareness.repo_index import CodeChunk, RepoIndex
from backend.app.models.awareness.system_snapshot import SystemSnapshot

# Cognition domain
from backend.app.models.cognition.agent import Agent, AgentFeedback, AgentRun, AgentStep
from backend.app.models.cognition.confidence_score import ConfidenceScore
from backend.app.models.cognition.error_analysis import ErrorAnalysis
from backend.app.models.cognition.hypothesis import Hypothesis
from backend.app.models.cognition.task_plan import TaskPlan
from backend.app.models.execution.tool_execution import ToolExecution
from backend.app.models.execution.workflow import Workflow

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
from backend.app.models.memory.episodic import EpisodicMemory
from backend.app.models.memory.graph import GraphEdge, GraphNode
from backend.app.models.memory.long_term_memory import LongTermMemory
from backend.app.models.memory.memory_graph import MemoryEdge, MemoryNode
from backend.app.models.memory.path_index import PathIndex
from backend.app.models.memory.semantic import SemanticMemory
from backend.app.models.memory.storage_registry import StorageRegistry
from backend.app.models.memory.working import WorkingMemory

# Privacy domain
from backend.app.models.privacy.auth_event import AuthEvent
from backend.app.models.privacy.user_settings import UserModelSettings

# System domain — v1.02 new models
from backend.app.models.system.agent_run_event import AgentRunEvent, AgentRunToolCall
from backend.app.models.system.mcp_server import MCPServer, MCPServerTool
from backend.app.models.system.observability import (  # noqa: F401
    PerformanceBaseline,
    TokenUsage,
    ToolExecutionMetrics,
)

__all__ = [
    # Memory
    "Document",
    "DocumentChunk",
    "DocumentType",
    "EpisodicMemory",
    "GraphEdge",
    "GraphNode",
    "LongTermMemory",
    "MemoryEdge",
    "MemoryNode",
    "PathIndex",
    "SemanticMemory",
    "StorageRegistry",
    "WorkingMemory",
    # Awareness
    "AttentionTracker",
    "ContextEvent",
    "ContextRule",
    "ContextState",
    "IndexedFile",
    "IndexingConfig",
    "CodeChunk",
    "RepoIndex",
    "SystemSnapshot",
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
    "ConfidenceScore",
    "ErrorAnalysis",
    "Hypothesis",
    "TaskPlan",
    # Execution
    "ToolExecution",
    "Workflow",
    # Privacy
    "AuthEvent",
    "UserModelSettings",
    # Integration
    "SyncState",
    # System — v1.02
    "MCPServer",
    "MCPServerTool",
    "AgentRunEvent",
    "AgentRunToolCall",
    "TokenUsage",
    "ToolExecutionMetrics",
    "PerformanceBaseline",
]
