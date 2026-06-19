"""Canonical system path definitions for Cortex.

All system-owned files must live under:
  ProjectRoot/CortexMemory/{db,logs,cache,runtime}
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Final

from backend.app.core.config import settings
from backend.app.core.paths import PROJECT_ROOT

# ── Exceptions ────────────────────────────────────────────────────────


class SecurityError(PermissionError):
    """Raised when a path violates system/user isolation boundaries."""


# ========== LINUX BLOCKED PATHS ==========
LINUX_BLOCKED_SYSTEM_PATHS: Final[set[str]] = {
    "/sys",
    "/proc",
    "/dev",
    "/run",
    "/boot",
    "/root",
    "/bin",
    "/sbin",
    "/usr",
    "/var",
    "/lib",
    "/lib64",
    "/etc",
    "/opt",
    "/srv",
    "/vm",
    "/mnt",
}

LINUX_IGNORED_DIRS: Final[set[str]] = {
    "__pycache__",
    ".venv",
    "venv",
    ".cortex",
    ".pytest_cache",
    "node_modules",
    ".git",
    ".env",
}

# ========== MACOS BLOCKED PATHS ==========
MACOS_BLOCKED_SYSTEM_PATHS: Final[set[str]] = {
    "/System",
    "/Library",
    "/private",
    "/dev",
    "/cores",
    "/usr/local/bin",
    "/usr/bin",
    "/bin",
    "/sbin",
    "/var",
}

MACOS_IGNORED_DIRS: Final[set[str]] = {
    "__pycache__",
    ".venv",
    "venv",
    ".cortex",
    ".pytest_cache",
    "node_modules",
    ".git",
    ".env",
    ".DS_Store",
}

# ========== WINDOWS BLOCKED PATHS ==========
WINDOWS_BLOCKED_SYSTEM_PATHS: Final[set[str]] = {
    "C:\\Windows",
    "C:\\System32",
    "C:\\Program Files",
    "C:\\Program Files (x86)",
    "C:\\ProgramData",
    "C:\\$Recycle.Bin",
    "C:\\System Volume Information",
}

WINDOWS_IGNORED_DIRS: Final[set[str]] = {
    "__pycache__",
    ".venv",
    "venv",
    ".cortex",
    ".pytest_cache",
    "node_modules",
    ".git",
    ".env",
}

COMMON_IGNORED_DIRS: Final[set[str]] = {
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".env",
    ".cortex",
    ".pytest_cache",
    "node_modules",
    ".git",
    ".gitignore",
    ".github",
    "dist",
    "build",
    "*.egg-info",
    ".mypy_cache",
    ".tox",
    "htmlcov",
    ".coverage",
    ".idea",
    ".vscode",
}

IGNORED_EXTENSIONS: Final[set[str]] = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".so",
    ".o",
    ".a",
    ".lib",
    ".dll",
    ".exe",
    ".bin",
    ".iso",
    ".dmg",
    ".zip",
    ".tar",
    ".gz",
    ".rar",
    ".7z",
    ".bak",
    ".tmp",
    ".log",
    ".lock",
    ".cache",
}

MAX_FILE_SIZE_BYTES: Final[int] = 1024 * 1024 * 1024
MAX_TOTAL_SCAN_SIZE_BYTES: Final[int] = 100 * 1024 * 1024 * 1024

SYSTEM_SUBDIRS: Final[dict[str, str]] = {
    "db": "db",
    "logs": "logs",
    "cache": "cache",
    "runtime": "runtime",
}

_SYSTEM_PATH_CACHE: dict[str, Path] | None = None


def get_cortex_root() -> Path:
    """Return the CortexMemory root directory.

    Per the storage architecture spec, all system/AI data lives under
    ``ProjectRoot/CortexMemory/`` — never inside ``.cortex/``.
    """
    root_value = settings.CORTEX_ROOT or os.environ.get("CORTEX_ROOT")
    if root_value:
        return Path(root_value).expanduser().resolve()
    return (PROJECT_ROOT / "CortexMemory").resolve()


def get_system_root() -> Path:
    """System root is the CortexMemory directory itself."""
    root = get_cortex_root()
    root.mkdir(parents=True, exist_ok=True)
    return root


@lru_cache(maxsize=1)
def _blocked_system_paths() -> set[str]:
    import platform

    system = platform.system()
    if system == "Darwin":
        return set(MACOS_BLOCKED_SYSTEM_PATHS)
    if system == "Windows":
        return set(WINDOWS_BLOCKED_SYSTEM_PATHS)
    return set(LINUX_BLOCKED_SYSTEM_PATHS)


def get_blocked_system_paths() -> set[str]:
    return _blocked_system_paths()


def _build_system_paths() -> dict[str, Path]:
    root = get_system_root()
    mapping = {key: (root / relative).resolve() for key, relative in SYSTEM_SUBDIRS.items()}
    for path in mapping.values():
        path.mkdir(parents=True, exist_ok=True)
    return mapping


def ensure_system_dirs() -> dict[str, Path]:
    global _SYSTEM_PATH_CACHE
    _SYSTEM_PATH_CACHE = _build_system_paths()
    return dict(_SYSTEM_PATH_CACHE)


def get_system_paths() -> dict[str, Path]:
    global _SYSTEM_PATH_CACHE
    if _SYSTEM_PATH_CACHE is None:
        _SYSTEM_PATH_CACHE = _build_system_paths()
    return dict(_SYSTEM_PATH_CACHE)


def get_system_path(name: str) -> Path:
    paths = get_system_paths()
    if name not in paths:
        raise KeyError(f"Unknown system path: {name}")
    return paths[name]
