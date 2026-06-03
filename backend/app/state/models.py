# backend/app/state/models.py

from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any, Dict, Optional


# -----------------------------
# EVENT TYPES (selective logging)
# -----------------------------
class EventType(str, Enum):
    FILE_INDEXED = "FILE_INDEXED"
    FILE_CHANGED = "FILE_CHANGED"
    TOOL_EXECUTED = "TOOL_EXECUTED"
    MEMORY_STORED = "MEMORY_STORED"
    RAG_UPDATED = "RAG_UPDATED"
    EXECUTION_COMPLETED = "EXECUTION_COMPLETED"


# -----------------------------
# EVENT MODEL
# -----------------------------
class SystemEvent(BaseModel):
    id: Optional[str] = None
    type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    payload: Dict[str, Any] = {}
    source: str = "system"


# -----------------------------
# SNAPSHOT STATE MODELS
# -----------------------------
class FileSystemState(BaseModel):
    indexed_files: Dict[str, float] = {}  # path -> last modified
    last_scan: Optional[datetime] = None


class AIState(BaseModel):
    last_queries: list[str] = []
    recent_tools: list[str] = []
    last_execution_id: Optional[str] = None


class SystemHealthState(BaseModel):
    status: str = "healthy"
    last_updated: datetime = Field(default_factory=datetime.utcnow)


# -----------------------------
# ROOT STATE OBJECT
# -----------------------------
class SystemState(BaseModel):
    filesystem: FileSystemState = FileSystemState()
    ai: AIState = AIState()
    health: SystemHealthState = SystemHealthState()