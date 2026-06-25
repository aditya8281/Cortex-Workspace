"""Python normalizer — converts raw extracted dicts into EntityBase entities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.agents.integrity.extractors._base import (
    CollectorPlugin,
    Normalizer,
)
from backend.app.agents.integrity.model._base import EntityBase


@dataclass(frozen=True)
class FileEntity(EntityBase):
    path: str = ""
    entity_type: str = "file"
    raw_metadata: dict[str, Any] | None = None


class PythonNormalizer(Normalizer):
    def __init__(self) -> None:
        super().__init__(
            CollectorPlugin(
                name="python-normalizer",
                plugin_version="1.0",
                supported_rkm_version="1.x",
            )
        )

    def normalize(self, raw: dict[str, Any]) -> list[EntityBase]:
        entities: list[EntityBase] = []

        # File-level entity
        file_entity = FileEntity(
            path=raw.get("path", ""),
            entity_type="python_file",
            raw_metadata={
                "classes": raw.get("classes", []),
                "functions": raw.get("functions", []),
                "imports": raw.get("imports", []),
            },
            source_collector="python",
            source_version="1.0",
        )
        entities.append(file_entity)

        # Per-class entities
        for cls_name in raw.get("classes", []):
            class_entity = FileEntity(
                entity_type="python_class",
                path=raw.get("path", ""),
                raw_metadata={"name": cls_name},
                source_collector="python",
                source_version="1.0",
            )
            entities.append(class_entity)

        return entities
