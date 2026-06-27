"""ImportGraphEngine — detect circular imports and import patterns."""

from __future__ import annotations

import sys
from typing import Any

from backend.app.agents.integrity.engines._base import Capability, IntegrityEngine
from backend.app.agents.integrity.model.context import (
    Classification,
    ExecutionProfile,
    IntegrityDomain,
    Priority,
    Severity,
)
from backend.app.agents.integrity.model.finding import Finding
from backend.app.agents.integrity.registry import register

# Standard library modules — never flag these as import hotspots.
_STDLIB: set[str] = set(sys.stdlib_module_names)


def _is_stdlib(module_name: str) -> bool:
    """Check if a module name refers to a standard library module."""
    root = module_name.split(".")[0]
    return root in _STDLIB


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

        # Collect: imported_module -> set of source files that import it.
        import_map: dict[str, set[str]] = {}
        for imp in imports:
            if isinstance(imp, dict):
                source = imp.get("file", "")
                module = imp.get("import", "")
            else:
                source = getattr(imp, "file", "")
                module = getattr(imp, "module", getattr(imp, "import", ""))

            if not module:
                continue
            import_map.setdefault(module, set()).add(source)

        # 1) Import hotspots — project-internal modules imported by many files.
        THRESHOLD = 10
        for module, sources in import_map.items():
            if _is_stdlib(module):
                continue
            if len(sources) >= THRESHOLD:
                findings.append(
                    Finding(
                        title="Import hotspot — module imported by many files",
                        description=(
                            f"'{module}' is imported by {len(sources)} different source files. "
                            f"Consider whether it should be split or restructured."
                        ),
                        severity=Severity.LOW,
                        priority=Priority.P3,
                        urgency=3,
                        classification=Classification.INCONSISTENT,
                        location=module,
                    )
                )

        return findings
