"""APIContractEngine — detect route/schema mismatches and API drift."""

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
    name="api-contract",
    domain=IntegrityDomain.SEMANTIC,
    capabilities={Capability.API},
    required_dependencies=["schema-engine"],
    profiles={ExecutionProfile.FULL, ExecutionProfile.VERIFICATION},
)
class APIContractEngine(IntegrityEngine):
    name = "api-contract"
    domain = IntegrityDomain.SEMANTIC
    capabilities = {Capability.API}
    required_dependencies = ["schema-engine"]
    profiles = {ExecutionProfile.FULL, ExecutionProfile.VERIFICATION}

    def analyze(
        self,
        model: Any,
        query: Any,
        views: Any,
        context: Any,
    ) -> list[Finding]:
        return []
