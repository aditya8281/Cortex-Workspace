"""Documentation model — plans, source-of-truths, ADRs."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DocumentationModel:
    plans: dict[uuid.UUID, Any]
    source_of_truths: dict[uuid.UUID, Any]
    adrs: list[Any]
