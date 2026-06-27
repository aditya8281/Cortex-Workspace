"""CrossLayerEngine — detect frontend/backend field naming inconsistencies."""

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
    name="cross-layer",
    domain=IntegrityDomain.SEMANTIC,
    capabilities={Capability.API, Capability.SCHEMA},
    required_dependencies=["schema-engine", "api-contract"],
    profiles={ExecutionProfile.FULL, ExecutionProfile.VERIFICATION},
)
class CrossLayerEngine(IntegrityEngine):
    name = "cross-layer"
    domain = IntegrityDomain.SEMANTIC
    capabilities = {Capability.API, Capability.SCHEMA}
    required_dependencies = ["schema-engine", "api-contract"]
    profiles = {ExecutionProfile.FULL, ExecutionProfile.VERIFICATION}

    def analyze(
        self,
        model: Any,
        query: Any,
        views: Any,
        context: Any,
    ) -> list[Finding]:
        findings: list[Finding] = []
        if not model or not hasattr(model, "code") or not query:
            return findings

        schemas = getattr(model.code, "schemas", {})
        for sid, schema in schemas.items():
            name = getattr(schema, "name", "") if hasattr(schema, "name") else ""
            if not name:
                continue
            fields = getattr(schema, "fields", []) if hasattr(schema, "fields") else []
            for field in fields:
                fname = getattr(field, "name", "") if hasattr(field, "name") else ""
                if not fname:
                    continue
                # Check naming consistency across layers
                if fname != fname.lower():
                    location = getattr(schema, "location", str(sid)) if hasattr(schema, "location") else str(sid)
                    findings.append(
                        Finding(
                            title=(f"Inconsistent field naming: {name}.{fname}"),
                            description=(f"Field '{fname}' in schema '{name}' uses non-standard casing"),
                            severity=Severity.LOW,
                            priority=Priority.P3,
                            urgency=2,
                            classification=Classification.INCONSISTENT,
                            location=location,
                        )
                    )

        return findings
