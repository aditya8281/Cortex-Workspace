from pathlib import Path
from backend.app.core.config import settings


class RepoScanner:
    """
    Scans repository and collects files for indexing.
    """

    def __init__(self):
        workspace = Path(settings.WORKSPACE_ROOT).resolve()
        self.search_paths = [workspace]
        
        downloads = Path.home() / "Downloads"
        if downloads.exists() and downloads not in self.search_paths:
            self.search_paths.append(downloads)

    def scan(self, root: str | None = None):
        import os
        files = []
        
        scan_roots = self.search_paths
        if root is not None:
            scan_roots = [Path(root).resolve()]

        ignored_dirs = {".git", "node_modules", "venv", ".venv", "__pycache__", ".cortex", "dist", "build", ".next"}

        for root_path in scan_roots:
            if not root_path.exists():
                continue
            for r, dirs, filenames in os.walk(root_path):
                # Prune hidden and ignored directories in-place so os.walk doesn't traverse them
                dirs[:] = [d for d in dirs if d not in ignored_dirs and not d.startswith(".")]
                
                for filename in filenames:
                    if filename.startswith("."):
                        continue
                    path = Path(r) / filename
                    if path.suffix in (".py", ".md", ".txt", ".pdf"):
                        files.append(str(path))

        return files
