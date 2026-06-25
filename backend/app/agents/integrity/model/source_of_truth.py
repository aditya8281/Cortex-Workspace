"""Source-of-Truth registry model — canonical data sources."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SourceOfTruth:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    name: str = ""
    entity_type: str = ""
    path: Path = Path(".")
    schema_version: str | None = None
    validation_rules: list[str] = field(default_factory=list)
