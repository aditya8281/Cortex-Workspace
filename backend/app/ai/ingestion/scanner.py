from pathlib import Path


class RepoScanner:
    """
    Scans repository and collects files for indexing.
    """

    def scan(self, root: str):
        files = []
        root_path = Path(root)

        for path in root_path.rglob("*"):
            if path.is_file():
                # Exclude hidden directories (starting with '.') and dependency directories
                parts = path.relative_to(root_path).parts
                if any(p.startswith(".") or p in ("venv", "node_modules", "__pycache__") for p in parts):
                    continue

                if path.suffix in (".py", ".md", ".txt"):
                    files.append(str(path))

        return files