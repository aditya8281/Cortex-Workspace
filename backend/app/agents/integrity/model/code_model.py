"""Code model — files, symbols, imports, schemas, types, routes, etc."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CodeModel:
    files: dict[uuid.UUID, Any]
    directories: set[Path]
    symbols: dict[uuid.UUID, Any]
    imports: list[Any]
    schemas: dict[uuid.UUID, Any]
    types: dict[uuid.UUID, Any]
    routes: dict[uuid.UUID, Any]
    routers: dict[uuid.UUID, Any]
    middleware: dict[uuid.UUID, Any]
    models: dict[uuid.UUID, Any]
    migrations: dict[uuid.UUID, Any]
    db_config: Any | None
    components: dict[uuid.UUID, Any]
    api_clients: dict[uuid.UUID, Any]
    configs: dict[uuid.UUID, Any]
