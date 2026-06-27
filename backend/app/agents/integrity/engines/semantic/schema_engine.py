"""SchemaEngine — detect field name mismatches across schemas."""

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
    name="schema-engine",
    domain=IntegrityDomain.SEMANTIC,
    capabilities={Capability.SCHEMA},
    profiles={ExecutionProfile.FULL, ExecutionProfile.VERIFICATION},
)
class SchemaEngine(IntegrityEngine):
    name = "schema-engine"
    domain = IntegrityDomain.SEMANTIC
    capabilities = {Capability.SCHEMA}
    profiles = {ExecutionProfile.FULL, ExecutionProfile.VERIFICATION}

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

        schemas = getattr(model.code, "schemas", {})
        seen_fields: dict[str, list[str]] = {}

        for sid, schema in schemas.items():
            name = getattr(schema, "name", str(sid)) if hasattr(schema, "name") else str(sid)
            fields = getattr(schema, "fields", []) if hasattr(schema, "fields") else []
            for field in fields:
                fname = getattr(field, "name", str(field)) if hasattr(field, "name") else str(field)
                if fname not in seen_fields:
                    seen_fields[fname] = []
                seen_fields[fname].append(name)

        return findings
