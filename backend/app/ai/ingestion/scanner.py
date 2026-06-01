import os
from pathlib import Path
from typing import List, Dict


SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".py"}


class FileScanner:
    def __init__(self, root_paths: List[str]):
        self.root_paths = root_paths

    def scan(self) -> List[Dict]:
        files = []

        for root in self.root_paths:
            for path in Path(root).rglob("*"):
                if path.is_file() and path.suffix in SUPPORTED_EXTENSIONS:
                    files.append({
                        "path": str(path),
                        "type": path.suffix,
                        "name": path.name,
                        "size": path.stat().st_size,
                        "modified_at": path.stat().st_mtime,
                    })

        return files