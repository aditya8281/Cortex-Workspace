"""DependencyEngine — analyze dependency structure and cycles."""

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
    name="dependency",
    domain=IntegrityDomain.STRUCTURAL,
    capabilities={Capability.DEPENDENCY, Capability.GRAPH},
    profiles={ExecutionProfile.FULL, ExecutionProfile.INCREMENTAL},
)
class DependencyEngine(IntegrityEngine):
    name = "dependency"
    domain = IntegrityDomain.STRUCTURAL
    capabilities = {Capability.DEPENDENCY, Capability.GRAPH}
    profiles = {ExecutionProfile.FULL, ExecutionProfile.INCREMENTAL}

    def analyze(
        self,
        model: Any,
        query: Any,
        views: Any,
        context: Any,
    ) -> list[Finding]:
        return []
