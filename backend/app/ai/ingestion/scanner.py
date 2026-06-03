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
        workspace = Path(settings.WORKSPACE_ROOT).resolve()
        self.discovery = FilesystemDiscovery()
        self.exclusions = default_exclusions
        self.search_paths = self.discovery.discover_roots()

        if workspace.exists() and workspace not in self.search_paths:
            self.search_paths.insert(0, workspace)

    def scan(self, root: str | None = None):
        files: list[str] = []
        seen: set[str] = set()

        scan_roots = self.search_paths
        exclusions = self.exclusions
        if root is not None:
            scan_roots = [Path(root).resolve()]
            exclusions = ExclusionConfig(
                ignored_dir_names=self.exclusions.ignored_dir_names,
                ignored_path_prefixes=(),
                index_extensions=self.exclusions.index_extensions,
                max_file_bytes=self.exclusions.max_file_bytes,
            )

        for root_path in scan_roots:
            if not root_path.exists():
                continue
            if exclusions.should_skip_path(root_path):
                continue

            for r, dirs, filenames in os.walk(root_path):
                parent = Path(r)
                if exclusions.should_skip_path(parent):
                    dirs.clear()
                    continue

                dirs[:] = [
                    d
                    for d in dirs
                    if not exclusions.should_prune_dir(d, parent)
                ]

                for filename in filenames:
                    path = parent / filename
                    if not exclusions.is_indexable_file(path):
                        continue
                    path_str = str(path.resolve())
                    if path_str in seen:
                        continue
                    seen.add(path_str)
                    files.append(path_str)

        return files

    def scan_incremental(self, changed_paths: list[str]) -> list[str]:
        """Return indexable files from a set of changed paths (files or directories)."""
        files: list[str] = []
        seen: set[str] = set()

        for raw in changed_paths:
            path = Path(raw).resolve()
            if not path.exists():
                continue
            if path.is_file():
                if self.exclusions.is_indexable_file(path):
                    path_str = str(path)
                    if path_str not in seen:
                        seen.add(path_str)
                        files.append(path_str)
                continue

            if self.exclusions.should_skip_path(path):
                continue

            for r, dirs, filenames in os.walk(path):
                parent = Path(r)
                dirs[:] = [
                    d
                    for d in dirs
                    if not self.exclusions.should_prune_dir(d, parent)
                ]
                for filename in filenames:
                    file_path = parent / filename
                    if not self.exclusions.is_indexable_file(file_path):
                        continue
                    path_str = str(file_path.resolve())
                    if path_str not in seen:
                        seen.add(path_str)
                        files.append(path_str)

        return files
