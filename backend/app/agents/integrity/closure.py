"""DependencyClosureService — impact set computation for changed files."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class DependencyEdge:
    source_id: uuid.UUID
    target_id: uuid.UUID
    reason: str = ""
    path: list[Any] = field(default_factory=list)


@dataclass
class ImpactSet:
    directly_changed: list[uuid.UUID] = field(default_factory=list)
    transitively_affected: list[uuid.UUID] = field(default_factory=list)
    dependency_chains: list[DependencyEdge] = field(default_factory=list)
    affected_symbols: list[str] = field(default_factory=list)
    affected_components: list[str] = field(default_factory=list)


class DependencyClosureService:
    """Compute the transitive dependency closure for a set of changed files."""

    def compute_impact_set(
        self,
        changed_files: list[Path],
        model: Any,
    ) -> ImpactSet:
        directly: list[uuid.UUID] = []

        for path in changed_files:
            matched = False
            if model and hasattr(model, "code"):
                for uid, finfo in model.code.files.items():
                    if hasattr(finfo, "path") and str(finfo.path) == str(path):
                        directly.append(uid)
                        matched = True
                        break
            if not matched:
                directly.append(uuid.uuid5(uuid.NAMESPACE_URL, str(path)))

        transitive: list[uuid.UUID] = []
        chains: list[DependencyEdge] = []

        if model and hasattr(model, "relationships"):
            for source_id in directly:
                seen: set[uuid.UUID] = {source_id}
                to_visit: list[uuid.UUID] = [source_id]
                while to_visit:
                    current = to_visit.pop(0)
                    for edge in model.relationships.edges:
                        if edge.source_id == current and edge.target_id not in seen:
                            seen.add(edge.target_id)
                            transitive.append(edge.target_id)
                            chains.append(
                                DependencyEdge(
                                    source_id=current,
                                    target_id=edge.target_id,
                                    reason=edge.type.value,
                                )
                            )
                            to_visit.append(edge.target_id)

        return ImpactSet(
            directly_changed=directly,
            transitively_affected=transitive,
            dependency_chains=chains,
        )
