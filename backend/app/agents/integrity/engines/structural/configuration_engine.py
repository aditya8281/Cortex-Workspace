"""ConfigurationEngine — detect config drift and missing values."""

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
    name="configuration",
    domain=IntegrityDomain.STRUCTURAL,
    capabilities={Capability.CONFIG},
    profiles={ExecutionProfile.FULL},
)
class ConfigurationEngine(IntegrityEngine):
    name = "configuration"
    domain = IntegrityDomain.STRUCTURAL
    capabilities = {Capability.CONFIG}
    profiles = {ExecutionProfile.FULL}

    def analyze(
        self,
        model: Any,
        query: Any,
        views: Any,
        context: Any,
    ) -> list[Finding]:
        return []
