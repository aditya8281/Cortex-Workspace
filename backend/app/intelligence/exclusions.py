"""Configurable filesystem exclusion rules for Cortex indexing."""

from __future__ import annotations

import json
import os
from pathlib import Path

from backend.app.core.paths import PROJECT_ROOT

DEFAULT_IGNORED_DIR_NAMES = frozenset(
    {
        ".git",
        "node_modules",
        "venv",
        ".venv",
        "__pycache__",
        ".cortex",
        "dist",
        "build",
        ".next",
        ".cache",
        ".local",
        ".npm",
        ".cargo",
        ".rustup",
        ".pyenv",
        ".nvm",
        "proc",
        "sys",
        "dev",
        "run",
        "tmp",
        "snap",
        "lost+found",
        "Trash",
        ".Trash",
    }
)

DEFAULT_IGNORED_PATH_PREFIXES = (
    "/proc",
    "/sys",
    "/dev",
    "/run",
    "/tmp",
    "/var/tmp",
    "/var/cache",
    "/var/log",
    "/boot",
    "/sbin",
    "/bin",
    "/lib",
    "/lib64",
    "/usr",
    "/opt",
    "/snap",
)

DEFAULT_INDEX_EXTENSIONS = frozenset(
    {".py", ".md", ".txt", ".pdf", ".rst", ".json", ".yaml", ".yml", ".toml", ".ipynb"}
)

CONFIG_FILENAME = ".cortex/exclusion_config.json"


class ExclusionConfig:
    def __init__(
        self,
        ignored_dir_names: frozenset[str] | None = None,
        ignored_path_prefixes: tuple[str, ...] | None = None,
        index_extensions: frozenset[str] | None = None,
        max_file_bytes: int = 20_000_000,
    ):
        self.ignored_dir_names = (
            DEFAULT_IGNORED_DIR_NAMES if ignored_dir_names is None else ignored_dir_names
        )
        self.ignored_path_prefixes = (
            DEFAULT_IGNORED_PATH_PREFIXES
            if ignored_path_prefixes is None
            else ignored_path_prefixes
        )
        self.index_extensions = (
            DEFAULT_INDEX_EXTENSIONS if index_extensions is None else index_extensions
        )
        self.max_file_bytes = max_file_bytes

    @classmethod
    def load(cls, config_path: Path | None = None) -> ExclusionConfig:
        if config_path is None:
            from backend.app.services.memory_manager import memory_manager
            path = memory_manager.get_path("sync_state", "exclusion_config.json")
        else:
            path = config_path
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return cls(
                ignored_dir_names=frozenset(data.get("ignored_dir_names", DEFAULT_IGNORED_DIR_NAMES)),
                ignored_path_prefixes=tuple(data.get("ignored_path_prefixes", DEFAULT_IGNORED_PATH_PREFIXES)),
                index_extensions=frozenset(data.get("index_extensions", DEFAULT_INDEX_EXTENSIONS)),
                max_file_bytes=int(data.get("max_file_bytes", 20_000_000)),
            )
        except Exception:
            return cls()

    def save(self, config_path: Path | None = None) -> None:
        if config_path is None:
            from backend.app.services.memory_manager import memory_manager
            path = memory_manager.get_path("sync_state", "exclusion_config.json")
        else:
            path = config_path
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "ignored_dir_names": sorted(self.ignored_dir_names),
            "ignored_path_prefixes": list(self.ignored_path_prefixes),
            "index_extensions": sorted(self.index_extensions),
            "max_file_bytes": self.max_file_bytes,
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def should_skip_path(self, path: Path) -> bool:
        resolved = path.resolve()
        path_str = str(resolved)
        for prefix in self.ignored_path_prefixes:
            if path_str == prefix or path_str.startswith(prefix + os.sep):
                return True
        return False

    def should_prune_dir(self, dirname: str, parent: Path) -> bool:
        if dirname in self.ignored_dir_names:
            return True
        if dirname.startswith("."):
            return True
        full = parent / dirname
        return self.should_skip_path(full)

    def is_indexable_file(self, path: Path) -> bool:
        if path.name.startswith("."):
            return False
        if path.suffix.lower() not in self.index_extensions:
            return False
        if self.should_skip_path(path):
            return False
        try:
            if path.stat().st_size > self.max_file_bytes:
                return False
        except OSError:
            return False
        return True


class ExclusionsProxy:
    @property
    def _target(self) -> ExclusionConfig:
        return ExclusionConfig.load()

    def __getattr__(self, name):
        return getattr(self._target, name)

    def should_skip_path(self, path: Path) -> bool:
        return self._target.should_skip_path(path)

    def should_prune_dir(self, dirname: str, parent: Path) -> bool:
        return self._target.should_prune_dir(dirname, parent)

    def is_indexable_file(self, path: Path) -> bool:
        return self._target.is_indexable_file(path)


default_exclusions = ExclusionsProxy()
