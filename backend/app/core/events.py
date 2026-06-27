"""Event types and Event dataclass — the backbone of cross-domain communication.

All events flow through the event bus. Domains publish events, other domains subscribe.
No direct imports between domain service layers — events are the only cross-domain channel.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


class EventDomain(enum.Enum):
    """Top-level event domain classification."""

    MEMORY = "memory"
    AWARENESS = "awareness"
    COGNITION = "cognition"
    EXECUTION = "execution"
    INTERACTION = "interaction"
    DEVELOPER = "developer"
    INTEGRATION = "integration"
    PRIVACY = "privacy"
    SYSTEM = "system"
    INTELLIGENCE = "intelligence"


class EventType(enum.Enum):
    """All event types across all domains. Format: domain.action."""

    # Memory events
    MEMORY_CREATED = "memory.created"
    MEMORY_UPDATED = "memory.updated"
    MEMORY_DELETED = "memory.deleted"
    MEMORY_CONSOLIDATED = "memory.consolidated"
    MEMORY_SEARCHED = "memory.searched"

    # Awareness events
    FILE_CHANGED = "awareness.file_changed"
    REPOSITORY_INDEXED = "awareness.repository_indexed"
    PROJECT_CHANGED = "awareness.project_changed"
    INDEX_COMPLETED = "awareness.index_completed"

    # Cognition events
    REASONING_STARTED = "cognition.reasoning_started"
    REASONING_COMPLETED = "cognition.reasoning_completed"
    PLANNING_STARTED = "cognition.planning_started"
    PLANNING_COMPLETED = "cognition.planning_completed"

    # Execution events
    TASK_STARTED = "execution.task_started"
    TASK_COMPLETED = "execution.task_completed"
    TASK_FAILED = "execution.task_failed"
    RUN_STARTED = "execution.run_started"
    RUN_COMPLETED = "execution.run_completed"
    RUN_FAILED = "execution.run_failed"

    # Interaction events
    MESSAGE_RECEIVED = "interaction.message_received"
    CONVERSATION_STARTED = "interaction.conversation_started"
    CONVERSATION_ENDED = "interaction.conversation_ended"
    NOTIFICATION_SENT = "interaction.notification_sent"
    USER_UPDATED = "interaction.user_updated"

    # Developer events
    REPO_CONNECTED = "developer.repo_connected"
    CATALOG_UPDATED = "developer.catalog_updated"

    # Integration events
    DOWNLOAD_COMPLETED = "integration.download_completed"
    SYNC_FINISHED = "integration.sync_finished"

    # Privacy events
    VAULT_UNLOCKED = "privacy.vault_unlocked"
    SETTINGS_CHANGED = "privacy.settings_changed"

    # System events
    HEALTH_CHECK = "system.health_check"
    SYSTEM_STARTUP = "system.system_startup"
    SYSTEM_SHUTDOWN = "system.system_shutdown"

    # Intelligence events
    MODEL_LOADED = "intelligence.model_loaded"
    MODEL_UNLOADED = "intelligence.model_unloaded"


@dataclass
class Event:
    """Immutable event object. All events flow through the event bus."""

    type: EventType
    source: str
    data: dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: int | None = None
    event_id: str | None = None  # UUID, set by bus on publish

    @property
    def domain(self) -> EventDomain:
        """Extract domain from event type (e.g., 'memory.created' -> 'memory')."""
        return EventDomain(self.type.value.split(".")[0])

    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "source": self.source,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "event_id": self.event_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Event:
        return cls(
            type=EventType(data["type"]),
            source=data["source"],
            data=data["data"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            user_id=data.get("user_id"),
            event_id=data.get("event_id"),
        )
