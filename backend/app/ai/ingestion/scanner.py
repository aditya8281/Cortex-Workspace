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
        files = []
        
        scan_roots = self.search_paths
        if root is not None:
            scan_roots = [Path(root).resolve()]

        for root_path in scan_roots:
            if not root_path.exists():
                continue
            for path in root_path.rglob("*"):
                if path.is_file():
                    # Exclude hidden directories (starting with '.') and dependency directories.
                    try:
                        relative_path = path.relative_to(root_path)
                        parts = relative_path.parts
                    except ValueError:
                        parts = path.parts

                    if any(
                        p.startswith(".") or p in ("venv", "node_modules", "__pycache__")
                        for p in parts
                    ):
                        continue

                    if path.suffix in (".py", ".md", ".txt", ".pdf"):
                        files.append(str(path))

        return files
