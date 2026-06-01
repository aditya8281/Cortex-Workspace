from pathlib import Path


class RepoScanner:
    """
    Scans repository and collects files for indexing.
    """

    def scan(self, root: str):
        files = []

        for path in Path(root).rglob("*"):
            if path.is_file():
                if any(x in str(path) for x in [".py", ".md", ".txt"]):
                    files.append(str(path))

        return files