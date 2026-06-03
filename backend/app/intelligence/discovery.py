"""Discover meaningful user content locations across the home directory."""

from __future__ import annotations

import os
from pathlib import Path

from backend.app.core.config import settings
from backend.app.intelligence.exclusions import ExclusionConfig, default_exclusions


class FilesystemDiscovery:
    """
    Intelligently discover useful indexing roots under the user's home directory.
    Does not rely on a fixed folder list — walks home and promotes high-value dirs.
    """

    PROMOTED_DIR_NAMES = frozenset(
        {
            "documents",
            "document",
            "downloads",
            "download",
            "desktop",
            "projects",
            "project",
            "workspace",
            "workspaces",
            "work",
            "development",
            "dev",
            "research",
            "notes",
            "notebooks",
            "code",
            "src",
            "repos",
            "repositories",
            "github",
            "gitlab",
            "learning",
            "courses",
            "papers",
            "writing",
        }
    )

    def __init__(self, exclusions: ExclusionConfig | None = None):
        self.exclusions = exclusions or default_exclusions
        self.home = Path.home().resolve()
        workspace = Path(settings.WORKSPACE_ROOT).resolve()
        self.workspace_root = workspace if workspace.exists() else Path.cwd().resolve()

    def discover_roots(self, max_roots: int = 48) -> list[Path]:
        roots: list[Path] = []
        seen: set[Path] = set()

        def add(path: Path) -> None:
            resolved = path.resolve()
            if resolved in seen or not resolved.exists():
                return
            if self.exclusions.should_skip_path(resolved):
                return
            seen.add(resolved)
            roots.append(resolved)

        add(self.workspace_root)
        add(self.home)

        if self.home.exists():
            self._scan_home_children(roots, seen, max_roots)

        return roots[:max_roots]

    def _scan_home_children(self, roots: list[Path], seen: set[Path], max_roots: int) -> None:
        try:
            entries = sorted(self.home.iterdir(), key=lambda p: p.name.lower())
        except OSError:
            return

        for entry in entries:
            if len(roots) >= max_roots:
                break
            if not entry.is_dir():
                continue
            if self.exclusions.should_prune_dir(entry.name, entry.parent):
                continue
            resolved = entry.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            roots.append(resolved)

            if entry.name.lower() in self.PROMOTED_DIR_NAMES:
                self._add_promoted_subdirs(entry, roots, seen, max_roots)

    def _add_promoted_subdirs(
        self, parent: Path, roots: list[Path], seen: set[Path], max_roots: int
    ) -> None:
        try:
            children = list(parent.iterdir())
        except OSError:
            return
        for child in children:
            if len(roots) >= max_roots:
                return
            if not child.is_dir():
                continue
            if self.exclusions.should_prune_dir(child.name, child.parent):
                continue
            if self._looks_like_project_dir(child):
                resolved = child.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    roots.append(resolved)

    def _looks_like_project_dir(self, path: Path) -> bool:
        markers = (
            ".git",
            "pyproject.toml",
            "package.json",
            "Cargo.toml",
            "go.mod",
            "pom.xml",
            "build.gradle",
            "requirements.txt",
            "README.md",
        )
        for marker in markers:
            if (path / marker).exists():
                return True
        return False

    def find_git_repositories(self, roots: list[Path] | None = None, limit: int = 200) -> list[Path]:
        scan_roots = roots or self.discover_roots()
        repos: list[Path] = []
        seen: set[Path] = set()

        for root in scan_roots:
            if len(repos) >= limit:
                break
            for dirpath, dirnames, _ in os.walk(root):
                parent = Path(dirpath)
                if self.exclusions.should_skip_path(parent):
                    dirnames.clear()
                    continue
                dirnames[:] = [
                    d
                    for d in dirnames
                    if not self.exclusions.should_prune_dir(d, parent)
                ]
                if (parent / ".git").is_dir():
                    resolved = parent.resolve()
                    if resolved not in seen:
                        seen.add(resolved)
                        repos.append(resolved)
                    dirnames.clear()

        return repos
