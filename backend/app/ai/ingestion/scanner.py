from pathlib import Path
from backend.app.core.config import settings


class RepoScanner:
    """
    Scans repository and collects files for indexing.
    """

    def __init__(self):
        workspace = Path(settings.WORKSPACE_ROOT).resolve()
        home = Path.home().resolve()
        self.search_paths = self._build_search_paths(workspace, home)

    def scan(self, root: str | None = None):
        import os
        files = []

        scan_roots = self.search_paths
        if root is not None:
            scan_roots = [Path(root).resolve()]

        ignored_dirs = {
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
            "proc",
            "sys",
            "dev",
            "run",
            "tmp",
        }

        for root_path in scan_roots:
            if not root_path.exists():
                continue
            for r, dirs, filenames in os.walk(root_path):
                # Prune hidden and ignored directories in-place so os.walk doesn't traverse them
                dirs[:] = [
                    d
                    for d in dirs
                    if d not in ignored_dirs and not d.startswith(".") and not self._is_system_noise(d)
                ]

                for filename in filenames:
                    if filename.startswith("."):
                        continue
                    path = Path(r) / filename
                    if path.suffix in (".py", ".md", ".txt", ".pdf"):
                        files.append(str(path))

        return files

    def _build_search_paths(self, workspace: Path, home: Path) -> list[Path]:
        search_paths = [workspace]
        common_roots = [
            home,
            home / "Desktop",
            home / "Documents",
            home / "Downloads",
            home / "Projects",
            home / "Work",
            home / "Development",
            home / "Research",
        ]

        for path in common_roots:
            if path.exists() and path not in search_paths:
                search_paths.append(path)

        return search_paths

    def _is_system_noise(self, directory: str) -> bool:
        return directory in {"proc", "sys", "dev", "run", "tmp"}
