from enum import Enum
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class EventType(str, Enum):
    FILE_INDEXED = "FILE_INDEXED"
    FILE_CHANGED = "FILE_CHANGED"
    TOOL_EXECUTED = "TOOL_EXECUTED"
    MEMORY_STORED = "MEMORY_STORED"
    RAG_UPDATED = "RAG_UPDATED"
    EXECUTION_COMPLETED = "EXECUTION_COMPLETED"


class SystemEvent(BaseModel):
    id: Optional[str] = None
    type: EventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: Dict[str, Any] = Field(default_factory=dict)
    source: str = "system"


class FileSystemState(BaseModel):
    indexed_files: Dict[str, float] = Field(default_factory=dict)
    last_scan: Optional[datetime] = None


class AIState(BaseModel):
    last_queries: list[str] = Field(default_factory=list)
    recent_tools: list[str] = Field(default_factory=list)
    last_execution_id: Optional[str] = None


class SystemHealthState(BaseModel):
    status: str = "healthy"
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SystemState(BaseModel):
    filesystem: FileSystemState = Field(default_factory=FileSystemState)
    ai: AIState = Field(default_factory=AIState)
    health: SystemHealthState = Field(default_factory=SystemHealthState)
