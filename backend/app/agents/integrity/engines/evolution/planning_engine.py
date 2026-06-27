"""PlanningEngine — detect planning drift against documentation."""

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
    name="planning",
    domain=IntegrityDomain.EVOLUTION,
    capabilities={Capability.PLANNING},
    required_dependencies=["documentation"],
    profiles={ExecutionProfile.FULL},
)
class PlanningEngine(IntegrityEngine):
    name = "planning"
    domain = IntegrityDomain.EVOLUTION
    capabilities = {Capability.PLANNING}
    required_dependencies = ["documentation"]
    profiles = {ExecutionProfile.FULL}

    def analyze(
        self,
        model: Any,
        query: Any,
        views: Any,
        context: Any,
    ) -> list[Finding]:
        return []
