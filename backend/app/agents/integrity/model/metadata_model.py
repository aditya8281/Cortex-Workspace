"""Metadata model — repository metadata and capabilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class RepositoryCapabilities:
    languages: set[str] = field(default_factory=set)
    frameworks: set[str] = field(default_factory=set)
    has_frontend: bool = False
    has_backend: bool = False
    has_database_migrations: bool = False
    has_docker: bool = False
    has_ci: bool = False


@dataclass(frozen=True)
class MetadataModel:
    version: str
    relationship_schema_version: str
    repository_hash: str
    generated_at: datetime
    collector_versions: dict[str, str] = field(default_factory=dict)
    capabilities: RepositoryCapabilities = field(
        default_factory=RepositoryCapabilities
    )
