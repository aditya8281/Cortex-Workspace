import os
import json
import platform
from pathlib import Path
from typing import List
from backend.app.core.config import settings
from backend.app.core.system_paths import (
    LINUX_BLOCKED_SYSTEM_PATHS,
    MACOS_BLOCKED_SYSTEM_PATHS,
    WINDOWS_BLOCKED_SYSTEM_PATHS,
)

# Module-level variable exposed for unit test mock patching compatibility
CONFIG_FILE = None

def get_config_file() -> Path:
    if CONFIG_FILE is not None:
        return Path(str(CONFIG_FILE))
    from backend.app.core import storage
    return storage.get_sync_root() / "sync_scope_config.json"


class SyncScopeConfig:
    def __init__(self):
        self.include_folders: List[str] = []
        self.exclude_folders: List[str] = []
        self.priority_folders: List[str] = []
        self.ignore_patterns: List[str] = [
            "*.tmp", "*.log", "node_modules", ".git", "build", "dist",
            "__pycache__", ".venv", "venv", ".cortex", ".pytest_cache"
        ]
        self.auto_sync_enabled: bool = True
        self._initialize_defaults()
        self.load()

    def _initialize_defaults(self):
        system = platform.system()
        home = str(Path.home().resolve())
        workspace = str(Path(settings.WORKSPACE_ROOT).resolve())

        def add_existing(paths: list[str], candidate: Path) -> None:
            if candidate.exists():
                resolved = str(candidate.resolve())
                if resolved not in paths:
                    paths.append(resolved)

        # Set default includes based on standard home directory children
        default_includes = []
        for child in [
            "Documents",
            "documents",
            "Desktop",
            "desktop",
            "Projects",
            "projects",
            "Downloads",
            "downloads",
        ]:
            add_existing(default_includes, Path(home) / child)
        if workspace not in default_includes:
            default_includes.append(workspace)
        self.include_folders = default_includes

        # Set default excludes based on system-protected locations (using constants)
        if system == "Linux":
            self.exclude_folders = list(LINUX_BLOCKED_SYSTEM_PATHS)
        elif system == "Darwin":  # macOS
            self.exclude_folders = list(MACOS_BLOCKED_SYSTEM_PATHS)
        elif system == "Windows":
            self.exclude_folders = list(WINDOWS_BLOCKED_SYSTEM_PATHS)
        else:
            # Fallback to Linux paths for unknown systems
            self.exclude_folders = list(LINUX_BLOCKED_SYSTEM_PATHS)

    def load(self):
        config_path = get_config_file()
        if not config_path.exists():
            self.save()
            return
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.include_folders = data.get("include_folders", self.include_folders)
                self.exclude_folders = data.get("exclude_folders", self.exclude_folders)
                self.priority_folders = data.get("priority_folders", self.priority_folders)
                self.ignore_patterns = data.get("ignore_patterns", self.ignore_patterns)
                self.auto_sync_enabled = data.get("auto_sync_enabled", self.auto_sync_enabled)
                self._augment_standard_includes()
        except Exception:
            self.save()

    def _augment_standard_includes(self):
        normalized: list[str] = []
        for folder in self.include_folders:
            if folder not in normalized:
                normalized.append(folder)

        home = Path.home().resolve()
        workspace = Path(settings.WORKSPACE_ROOT).resolve()
        for child in [
            "Documents",
            "documents",
            "Desktop",
            "desktop",
            "Projects",
            "projects",
            "Downloads",
            "downloads",
        ]:
            candidate = home / child
            if candidate.exists():
                resolved = str(candidate.resolve())
                if resolved not in normalized:
                    normalized.append(resolved)

        workspace_resolved = str(workspace)
        if workspace.exists() and workspace_resolved not in normalized:
            normalized.append(workspace_resolved)

        self.include_folders = normalized

    def save(self):
        config_path = get_config_file()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "include_folders": sorted(list(set(self.include_folders))),
            "exclude_folders": sorted(list(set(self.exclude_folders))),
            "priority_folders": sorted(list(set(self.priority_folders))),
            "ignore_patterns": sorted(list(set(self.ignore_patterns))),
            "auto_sync_enabled": self.auto_sync_enabled
        }
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def is_excluded(self, path_str: str, bypass_prefixes: List[str] | None = None) -> bool:
        resolved = Path(path_str).resolve()
        resolved_str = str(resolved)

        # 1. Check against explicit excludes
        for ex in self.exclude_folders:
            ex_resolved = Path(ex).resolve()
            ex_resolved_str = str(ex_resolved)
            if resolved_str == ex_resolved_str or resolved_str.startswith(ex_resolved_str + os.sep):
                should_bypass = False
                if bypass_prefixes:
                    for bp in bypass_prefixes:
                        bp_path = Path(bp).resolve()
                        if ex_resolved == bp_path or ex_resolved in bp_path.parents:
                            should_bypass = True
                            break
                if not should_bypass:
                    return True

        # 2. Check each part of the path for hidden or ignore patterns
        for part in resolved.parts:
            # Check hidden
            if part.startswith(".") and part != "." and part != "..":
                return True
            # Check ignore patterns against each part
            for pat in self.ignore_patterns:
                import fnmatch
                if fnmatch.fnmatch(part, pat):
                    return True

        return False
