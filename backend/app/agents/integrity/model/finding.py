"""Finding model — analysis results, candidate fixes."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any

from backend.app.agents.integrity.model.context import (
    Severity,
    Classification,
    Priority,
)


class FixType(enum.Enum):
    MANUAL = "manual"
    SCRIPT = "script"
    PATCH = "patch"


@dataclass(frozen=True)
class CandidateFix:
    fix_type: FixType = FixType.MANUAL
    fix_code: str | None = None
    autofix_available: bool = True
    estimated_effort: str = "minutes"
    breaking_change: bool = False


@dataclass(frozen=True)
class Finding:
    id: str = ""
    title: str = ""
    description: str = ""
    severity: Severity = Severity.INSIGHT
    priority: Priority = Priority.P3
    urgency: int = 1
    classification: Classification = Classification.INCONSISTENT
    location: str = ""
    affected_components: list[str] = field(default_factory=list)
    dependency_chain: list[str] = field(default_factory=list)
    root_cause: str = ""
    downstream_impact: str = ""
    recommendation: str = ""
    fix: CandidateFix | None = None
    confidence: float = 1.0
    related_findings: list[str] = field(default_factory=list)
    owner: str | None = None
    tags: set[str] = field(default_factory=set)
    references: list[str] = field(default_factory=list)
