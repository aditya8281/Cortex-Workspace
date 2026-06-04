import os
from pathlib import Path

from backend.app.core.config import settings
from backend.app.intelligence.discovery import FilesystemDiscovery
from backend.app.intelligence.exclusions import ExclusionConfig, default_exclusions


class RepoScanner:
    """
    Scans user environment and collects files for indexing.
    Uses intelligent home-directory discovery with configurable exclusions.
    """

    def __init__(self):
        self.discovery = FilesystemDiscovery()
        self.exclusions = default_exclusions

    def scan(self, root: str | None = None) -> list[str]:
        from backend.app.intelligence.scope_config import SyncScopeConfig
        config = SyncScopeConfig()
        from collections import deque
        import time

        files: list[str] = []
        seen_files: set[str] = set()
        seen_dirs: set[str] = set()

        if root is not None:
            roots = [Path(root).resolve()]
        else:
            # Load user defined inclusion root folders
            roots = [Path(p).resolve() for p in config.include_folders]
            if not roots:
                workspace = Path(settings.WORKSPACE_ROOT).resolve()
                if workspace.exists():
                    roots.append(workspace)

        bypass_prefixes = [str(r) for r in roots]

        queue = deque()
        for r in roots:
            if r.exists() and r.is_dir() and not config.is_excluded(str(r), bypass_prefixes=bypass_prefixes):
                queue.append((r, 0))  # (directory_path, depth)
                seen_dirs.add(str(r))

        max_depth = 15
        batch_count = 0

        while queue:
            curr_dir, depth = queue.popleft()
            batch_count += 1
            if batch_count % 100 == 0:
                time.sleep(0.005)  # minor yield to prevent CPU/Disk lockup

            if depth > max_depth:
                continue

            try:
                for entry in curr_dir.iterdir():
                    if config.is_excluded(str(entry), bypass_prefixes=bypass_prefixes):
                        continue

                    if entry.is_dir():
                        resolved_dir = str(entry.resolve())
                        if resolved_dir not in seen_dirs:
                            seen_dirs.add(resolved_dir)
                            queue.append((entry, depth + 1))
                    elif entry.is_file():
                        suffix = entry.suffix.lower()
                        if suffix in self.exclusions.index_extensions:
                            try:
                                if entry.stat().st_size <= self.exclusions.max_file_bytes:
                                    resolved_file = str(entry.resolve())
                                    if resolved_file not in seen_files:
                                        seen_files.add(resolved_file)
                                        files.append(resolved_file)
                            except OSError:
                                continue
            except OSError:
                continue

        return files

    def scan_incremental(self, changed_paths: list[str]) -> list[str]:
        """Return indexable files from a set of changed paths (files or directories)."""
        from backend.app.intelligence.scope_config import SyncScopeConfig
        config = SyncScopeConfig()

        inclusion_roots = [Path(p).resolve() for p in config.include_folders]
        if not inclusion_roots:
            workspace = Path(settings.WORKSPACE_ROOT).resolve()
            if workspace.exists():
                inclusion_roots.append(workspace)
        
        bypass_prefixes = [str(r) for r in inclusion_roots] + [str(Path(raw).resolve()) for raw in changed_paths]

        files: list[str] = []
        seen: set[str] = set()

        for raw in changed_paths:
            path = Path(raw).resolve()
            if not path.exists():
                continue
            if path.is_file():
                if path.suffix.lower() in self.exclusions.index_extensions and not config.is_excluded(str(path), bypass_prefixes=bypass_prefixes):
                    try:
                        if path.stat().st_size <= self.exclusions.max_file_bytes:
                            path_str = str(path)
                            if path_str not in seen:
                                seen.add(path_str)
                                files.append(path_str)
                    except OSError:
                        pass
                continue

            if config.is_excluded(str(path), bypass_prefixes=bypass_prefixes):
                continue

            for r, dirs, filenames in os.walk(path):
                parent = Path(r)
                dirs[:] = [
                    d
                    for d in dirs
                    if not config.is_excluded(str(parent / d), bypass_prefixes=bypass_prefixes)
                ]
                for filename in filenames:
                    file_path = parent / filename
                    if file_path.suffix.lower() not in self.exclusions.index_extensions:
                        continue
                    if config.is_excluded(str(file_path), bypass_prefixes=bypass_prefixes):
                        continue
                    try:
                        if file_path.stat().st_size > self.exclusions.max_file_bytes:
                            continue
                    except OSError:
                        continue
                    path_str = str(file_path.resolve())
                    if path_str not in seen:
                        seen.add(path_str)
                        files.append(path_str)

        return files
