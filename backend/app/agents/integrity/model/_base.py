from __future__ import annotations
import uuid
from dataclasses import dataclass, field


@dataclass(frozen=True)
class EntityBase:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    confidence: float = 1.0
    source_collector: str = "unknown"
    source_version: str = "0.1"
