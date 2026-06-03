from pathlib import Path
from typing import List

from backend.app.core.config import settings
from backend.app.intelligence.discovery import FilesystemDiscovery
from backend.app.intelligence.exclusions import default_exclusions


class FileSearchAgent:
    """
    Agent for searching local file system contents across discovered user paths.
    """

    def __init__(self, workspace_root: str | None = None):
        if workspace_root is None:
            workspace_root = settings.WORKSPACE_ROOT
        self.workspace_root = Path(workspace_root).resolve()
        discovery = FilesystemDiscovery()
        self.search_paths = discovery.discover_roots()
        if self.workspace_root.exists() and self.workspace_root not in self.search_paths:
            self.search_paths.insert(0, self.workspace_root)

    def search(self, query: str) -> str:
        """
        Search files in configured paths for query keywords.
        """
        query_words = [w.lower() for w in query.split() if len(w) > 3]
        if not query_words:
            return "FileSearchAgent: Query is too short or generic. Please provide specific keywords."

        matched_files: List[str] = []
        file_count = 0

        import os

        for root in self.search_paths:
            if not root.exists() or default_exclusions.should_skip_path(root):
                continue
            for r, dirs, filenames in os.walk(root):
                parent = Path(r)
                dirs[:] = [
                    d
                    for d in dirs
                    if not default_exclusions.should_prune_dir(d, parent)
                ]

                for filename in filenames:
                    path = parent / filename
                    if not default_exclusions.is_indexable_file(path) and path.suffix not in (
                        ".py",
                        ".md",
                        ".txt",
                        ".toml",
                        ".pdf",
                    ):
                        continue
                    file_count += 1

                    try:
                        relative_path = path.relative_to(root)
                    except ValueError:
                        relative_path = path

                    path_display = str(path) if root != self.workspace_root else str(relative_path)

                    if any(w in path_display.lower() for w in query_words):
                        matched_files.append(f"- [File] {path_display}")
                        continue

                    if path.suffix in (".py", ".md", ".txt", ".toml", ".pdf") and path.stat().st_size < 5_000_000:
                        try:
                            if path.suffix == ".pdf":
                                import fitz

                                doc = fitz.open(path)
                                content = ""
                                for page in doc:
                                    content += page.get_text()
                            else:
                                content = path.read_text(encoding="utf-8", errors="ignore")

                            if any(w in content.lower() for w in query_words):
                                matched_files.append(f"- [Content Match] {path_display}")
                        except Exception:
                            pass

                if file_count > 50000:
                    break

        if not matched_files:
            return (
                f"FileSearchAgent: Searched {file_count} files across "
                f"{len(self.search_paths)} roots but found no matches for: {', '.join(query_words)}"
            )

        results_str = "\n".join(matched_files[:10])
        total_matches = len(matched_files)
        suffix = f"\n... and {total_matches - 10} more files." if total_matches > 10 else ""
        return f"FileSearchAgent found {total_matches} matches:\n{results_str}{suffix}"
