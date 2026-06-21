"""Model search engine — natural language queries and filter-based search."""

from __future__ import annotations

import logging

from sqlalchemy import String as sa_String
from sqlalchemy import cast as sa_cast
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.app.models.model_catalog import ModelCatalog

logger = logging.getLogger(__name__)


class ModelSearchService:
    """Search models by text, filters, and natural language queries."""

    NL_MAPPINGS = {
        "best coding": {"capabilities": ["code"], "sort": "popularity"},
        "coding model": {"capabilities": ["code"]},
        "vision model": {"capabilities": ["vision"]},
        "small model": {"max_params": 4.0},
        "large model": {"min_params": 30.0},
        "fast model": {"sort": "speed"},
        "lightweight": {"max_params": 4.0},
        "embedding": {"capabilities": ["embedding"]},
        "reasoning": {"capabilities": ["reasoning"]},
        "tool use": {"capabilities": ["tool_use"]},
    }

    def __init__(self, db: Session):
        self._db = db

    def search(self, query: str, limit: int = 50) -> list[ModelCatalog]:
        """Search models by text query with natural language understanding."""
        filters = self._parse_natural_language(query)

        if filters:
            return self._filtered_search(filters, limit)

        return self._text_search(query, limit)

    def filter(
        self,
        capabilities: list[str] | None = None,
        min_params: float | None = None,
        max_params: float | None = None,
        provider: str | None = None,
        family: str | None = None,
        sort: str = "relevance",
        limit: int = 50,
    ) -> list[ModelCatalog]:
        """Filter models by criteria."""
        q = self._db.query(ModelCatalog)

        if capabilities:
            for cap in capabilities:
                q = q.filter(sa_cast(ModelCatalog.capabilities, sa_String).like(f'%"{cap}"%'))
        if min_params is not None:
            q = q.filter(ModelCatalog.parameter_count >= min_params)
        if max_params is not None:
            q = q.filter(ModelCatalog.parameter_count <= max_params)
        if provider:
            q = q.filter(ModelCatalog.provider == provider)
        if family:
            q = q.filter(ModelCatalog.family == family)

        if sort == "popularity":
            q = q.order_by(ModelCatalog.total_downloads.desc())
        elif sort == "name":
            q = q.order_by(ModelCatalog.display_name)
        elif sort == "params":
            q = q.order_by(ModelCatalog.parameter_count)
        else:
            q = q.order_by(ModelCatalog.display_name)

        return q.limit(limit).all()

    def autocomplete(self, prefix: str, limit: int = 10) -> list[str]:
        """Autocomplete model names."""
        models = (
            self._db.query(ModelCatalog.display_name)
            .filter(ModelCatalog.display_name.ilike(f"{prefix}%"))
            .limit(limit)
            .all()
        )
        return [m.display_name for m in models]

    def _text_search(self, query: str, limit: int) -> list[ModelCatalog]:
        """Full-text search across model fields."""
        pattern = f"%{query}%"
        return (
            self._db.query(ModelCatalog)
            .filter(
                or_(
                    ModelCatalog.display_name.ilike(pattern),
                    ModelCatalog.family.ilike(pattern),
                    ModelCatalog.description.ilike(pattern),
                    ModelCatalog.model_id.ilike(pattern),
                )
            )
            .limit(limit)
            .all()
        )

    def _parse_natural_language(self, query: str) -> dict | None:
        """Parse natural language query into filter criteria."""
        query_lower = query.lower().strip()
        for phrase, filters in self.NL_MAPPINGS.items():
            if phrase in query_lower:
                return filters
        return None

    def _filtered_search(self, filters: dict, limit: int) -> list[ModelCatalog]:
        """Execute filtered search."""
        return self.filter(
            capabilities=filters.get("capabilities"),
            min_params=filters.get("min_params"),
            max_params=filters.get("max_params"),
            sort=filters.get("sort", "relevance"),
            limit=limit,
        )
