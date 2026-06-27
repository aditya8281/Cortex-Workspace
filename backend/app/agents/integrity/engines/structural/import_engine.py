"""ImportGraphEngine — detect circular imports and import patterns."""

from __future__ import annotations

from typing import Any

from backend.app.agents.integrity.engines._base import Capability, IntegrityEngine
from backend.app.agents.integrity.model.context import (
    ExecutionProfile,
    IntegrityDomain,
)
from backend.app.agents.integrity.model.finding import (
    Classification,
    Finding,
    Priority,
    Severity,
)
from backend.app.agents.integrity.registry import register


@register(
    name="import-graph",
    domain=IntegrityDomain.STRUCTURAL,
    capabilities={Capability.IMPORT, Capability.GRAPH},
    profiles={
        ExecutionProfile.FULL,
        ExecutionProfile.QUICK,
        ExecutionProfile.INCREMENTAL,
    },
)
class ImportGraphEngine(IntegrityEngine):
    name = "import-graph"
    domain = IntegrityDomain.STRUCTURAL
    capabilities = {Capability.IMPORT, Capability.GRAPH}
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
        findings: list[Finding] = []
        if not model or not hasattr(model, "code"):
            return findings

        imports = getattr(model.code, "imports", [])
        seen_modules: set[str] = set()

        for imp in imports:
            file = getattr(imp, "file", "") if hasattr(imp, "file") else str(imp)
            if file in seen_modules:
                findings.append(
                    Finding(
                        title="Potential circular import",
                        description=(f"File imported multiple times: {file}"),
                        severity=Severity.LOW,
                        priority=Priority.P3,
                        urgency=3,
                        classification=Classification.DUPLICATE,
                        location=file,
                    )
                )
            seen_modules.add(file)

        return findings
