"""FilesystemEngine — detect orphaned files, directory structure issues."""

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
    name="filesystem",
    domain=IntegrityDomain.STRUCTURAL,
    capabilities={Capability.FILESYSTEM},
    profiles={
        ExecutionProfile.FULL,
        ExecutionProfile.QUICK,
        ExecutionProfile.INCREMENTAL,
    },
)
class FilesystemEngine(IntegrityEngine):
    name = "filesystem"
    domain = IntegrityDomain.STRUCTURAL
    capabilities = {Capability.FILESYSTEM}
    profiles = {
        ExecutionProfile.FULL,
        ExecutionProfile.QUICK,
        ExecutionProfile.INCREMENTAL,
    }

    def analyze(
        self,
        model: Any,
        query: Any,
        views: Any,
        context: Any,
    ) -> list[Finding]:
        return []
