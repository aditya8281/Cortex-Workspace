"""Documentation model — plans, source-of-truths, ADRs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import uuid


@dataclass(frozen=True)
class DocumentationModel:
    plans: dict[uuid.UUID, Any]
    source_of_truths: dict[uuid.UUID, Any]
    adrs: list[Any]
