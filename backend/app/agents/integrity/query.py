"""RepositoryQueryService — graph traversal over RepositoryKnowledgeModel."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from backend.app.agents.integrity.model import RepositoryKnowledgeModel
from backend.app.agents.integrity.model._base import EntityBase
from backend.app.agents.integrity.model.relationship_model import (
    RelationshipType,
)


@dataclass
class ImpactSet:
    directly_changed: list[uuid.UUID] = field(default_factory=list)
    transitively_affected: list[uuid.UUID] = field(default_factory=list)
    affected_symbols: list[str] = field(default_factory=list)
    affected_components: list[str] = field(default_factory=list)


@dataclass
class DependencyEdge:
    source_id: uuid.UUID
    target_id: uuid.UUID
    reason: str = ""
    path: list[Any] = field(default_factory=list)


class RepositoryQueryService:
    """Graph query service over an RKM.

    Primary interface for engines to traverse the model. Engines should
    rarely access RKM dicts directly.
    """

    def __init__(self, model: RepositoryKnowledgeModel) -> None:
        self._model = model

    def find_routes(self, path_pattern: str | None = None) -> list[Any]:
        routes = list(self._model.code.routes.values())
        if path_pattern:
            return [r for r in routes if path_pattern in str(r)]
        return routes

    def find_schemas(self, field_name: str) -> list[Any]:
        return [
            s
            for s in self._model.code.schemas.values()
            if hasattr(s, "fields") and field_name in getattr(s, "fields", [])
        ]

    def find_by_id(self, entity_id: uuid.UUID) -> Any | None:
        for collection in [
            self._model.code.files,
            self._model.code.symbols,
            self._model.code.schemas,
            self._model.code.types,
            self._model.code.routes,
            self._model.code.models,
            self._model.code.migrations,
            self._model.ecosystem.commands,
            self._model.ecosystem.skills,
            self._model.ecosystem.hooks,
            self._model.ecosystem.workflows,
            self._model.ecosystem.plans,
        ]:
            if entity_id in collection:
                return collection[entity_id]
        return None

    def find_by_tag(self, tag: str) -> list[Any]:
        return []

    def find_consumers(
        self, entity_id: uuid.UUID
    ) -> list[EntityBase]:
        consumers: list[EntityBase] = []
        for edge in self._model.relationships.edges:
            if edge.target_id == entity_id:
                consumer = self.find_by_id(edge.source_id)
                if consumer:
                    consumers.append(consumer)
        return consumers

    def find_producers(
        self, entity_id: uuid.UUID
    ) -> list[EntityBase]:
        producers: list[EntityBase] = []
        for edge in self._model.relationships.edges:
            if edge.source_id == entity_id:
                producer = self.find_by_id(edge.target_id)
                if producer:
                    producers.append(producer)
        return producers

    def trace(
        self,
        entity_id: uuid.UUID,
        relationship_types: list[RelationshipType],
    ) -> list[EntityBase]:
        seen: set[uuid.UUID] = {entity_id}
        found: list[EntityBase] = []
        to_visit = [entity_id]
        rel_types = set(relationship_types)

        while to_visit:
            current = to_visit.pop(0)
            for edge in self._model.relationships.edges:
                if edge.type not in rel_types:
                    continue
                if edge.source_id == current and edge.target_id not in seen:
                    seen.add(edge.target_id)
                    target = self.find_by_id(edge.target_id)
                    if target:
                        found.append(target)
                        to_visit.append(edge.target_id)
        return found

    def find_dependencies(
        self,
        entity_id: uuid.UUID,
        *,
        transitive: bool = False,
    ) -> list[DependencyEdge]:
        results: list[DependencyEdge] = []
        seen: set[uuid.UUID] = {entity_id}
        to_visit = [entity_id]

        while to_visit:
            current = to_visit.pop(0)
            if current in seen:
                continue
            seen.add(current)
            for edge in self._model.relationships.edges:
                if edge.source_id == current:
                    results.append(
                        DependencyEdge(
                            source_id=edge.source_id,
                            target_id=edge.target_id,
                            reason=edge.type.value,
                        )
                    )
                    if transitive and edge.target_id not in seen:
                        to_visit.append(edge.target_id)
                if edge.target_id == current:
                    results.append(
                        DependencyEdge(
                            source_id=edge.source_id,
                            target_id=edge.target_id,
                            reason=edge.type.value,
                        )
                    )
                    if transitive and edge.source_id not in seen:
                        to_visit.append(edge.source_id)
        return results

    def find_impact(
        self, entity_ids: list[uuid.UUID]
    ) -> ImpactSet:
        return ImpactSet(directly_changed=list(entity_ids))
