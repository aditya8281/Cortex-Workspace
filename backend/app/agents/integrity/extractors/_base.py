"""Extractor/Normalizer base classes and CollectorPlugin."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from backend.app.agents.integrity.model._base import EntityBase


@dataclass
class CollectorPlugin:
    name: str
    plugin_version: str
    supported_rkm_version: str = "1.x"
    supported_language_version: str | None = None


class Extractor(ABC):
    def __init__(self, plugin: CollectorPlugin | None = None) -> None:
        self.plugin = plugin or CollectorPlugin(
            name="unknown", plugin_version="0.1"
        )

    @abstractmethod
    def extract(self, path: Path) -> dict[str, Any]: ...


class Normalizer(ABC):
    def __init__(self, plugin: CollectorPlugin | None = None) -> None:
        self.plugin = plugin or CollectorPlugin(
            name="unknown", plugin_version="0.1"
        )

    @abstractmethod
    def normalize(self, raw: dict[str, Any]) -> list[EntityBase]: ...
