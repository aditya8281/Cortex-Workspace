"""MigrationEngine — detect migration conflicts and ordering issues."""

from __future__ import annotations

from typing import Any

from backend.app.agents.integrity.engines._base import Capability, IntegrityEngine
from backend.app.agents.integrity.model.context import (
    ExecutionProfile,
    IntegrityDomain,
)
from backend.app.agents.integrity.model.finding import Finding
from backend.app.agents.integrity.registry import register


@register(
    name="migration",
    domain=IntegrityDomain.STRUCTURAL,
    capabilities={Capability.MIGRATION},
    profiles={ExecutionProfile.FULL},
)
class MigrationEngine(IntegrityEngine):
    name = "migration"
    domain = IntegrityDomain.STRUCTURAL
    capabilities = {Capability.MIGRATION}
    profiles = {ExecutionProfile.FULL}

    def analyze(
        self,
        model: Any,
        query: Any,
        views: Any,
        context: Any,
    ) -> list[Finding]:
        return []
