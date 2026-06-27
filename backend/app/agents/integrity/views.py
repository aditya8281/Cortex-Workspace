"""View registry — lazy, cached, invalidatable derived views from RKM."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class DerivedViews:
    import_graph: Any = None
    dependency_graph: Any = None
    api_graph: Any = None
    schema_graph: Any = None
    route_graph: Any = None
    migration_graph: Any = None
    configuration_graph: Any = None
    producer_consumer_graph: Any = None
    cross_layer_chain: Any = None


class ViewRegistry:
    """Manages derived views over an RKM with lazy build and invalidation."""

    def __init__(self) -> None:
        self._cache: DerivedViews | None = None
        self._valid = False

    def build(self, model: Any) -> DerivedViews:
        if self._valid and self._cache is not None:
            return self._cache

        views = DerivedViews()
        self._build_import_graph(views, model)
        self._build_dependency_graph(views, model)
        self._build_api_graph(views, model)
        self._build_schema_graph(views, model)
        self._build_route_graph(views, model)

        self._cache = views
        self._valid = True
        return views

    def invalidate(self) -> None:
        self._valid = False
        self._cache = None

    def _build_import_graph(self, views: DerivedViews, model: Any) -> None:
        edges = []
        if model and hasattr(model, "code"):
            for imp in model.code.imports:
                edges.append(imp)
        views.import_graph = {"edges": edges}

    def _build_dependency_graph(self, views: DerivedViews, model: Any) -> None:
        views.dependency_graph = {"nodes": [], "edges": []}

    def _build_api_graph(self, views: DerivedViews, model: Any) -> None:
        views.api_graph = {"routes": [], "schemas": []}

    def _build_schema_graph(self, views: DerivedViews, model: Any) -> None:
        views.schema_graph = {"schemas": []}

    def _build_route_graph(self, views: DerivedViews, model: Any) -> None:
        views.route_graph = {"routes": []}
