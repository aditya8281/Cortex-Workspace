"""Integrity engine interface — abstract base and capability model."""

from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from typing import Any

from backend.app.agents.integrity.model.context import (
    ExecutionProfile,
    IntegrityDomain,
)
from backend.app.agents.integrity.model.finding import Finding


class Capability(enum.Enum):
    SCHEMA = "schema"
    API = "api"
    CONFIG = "config"
    DOCS = "docs"
    GRAPH = "graph"
    IMPORT = "import"
    DEPENDENCY = "dependency"
    MIGRATION = "migration"
    FILESYSTEM = "filesystem"
    PLANNING = "planning"
    METRICS = "metrics"


class IntegrityEngine(ABC):
    name: str = ""
    domain: IntegrityDomain = IntegrityDomain.STRUCTURAL
    capabilities: set[Capability] = set()
    required_dependencies: list[str] = []
    optional_dependencies: list[str] = []
    profiles: set[ExecutionProfile] = set()

    @abstractmethod
    def analyze(
        self,
        model: Any,
        query: Any,
        views: Any,
        context: Any,
    ) -> list[Finding]: ...
