from pathlib import Path
from typing import List

from backend.app.core.config import settings


class FileSearchAgent:
    """
    Agent for searching local file system contents and list of files.
    """

    def __init__(self, workspace_root: str | None = None):
        if workspace_root is None:
            workspace_root = settings.WORKSPACE_ROOT
        self.workspace_root = Path(workspace_root).resolve()
        
        self.search_paths = [self.workspace_root]
        downloads = Path.home() / "Downloads"
        if downloads.exists() and downloads not in self.search_paths:
            self.search_paths.append(downloads)

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
        ignored_dirs = {".git", "node_modules", "venv", ".venv", "__pycache__", ".cortex", "dist", "build", ".next"}

        # Scan for matching files in all search paths
        for root in self.search_paths:
            if not root.exists():
                continue
            for r, dirs, filenames in os.walk(root):
                # Prune hidden and ignored directories in-place so os.walk doesn't traverse them
                dirs[:] = [d for d in dirs if d not in ignored_dirs and not d.startswith(".")]
                
                for filename in filenames:
                    if filename.startswith("."):
                        continue
                    path = Path(r) / filename
                    file_count += 1
                    
                    try:
                        relative_path = path.relative_to(root)
                    except ValueError:
                        relative_path = path

                    if root == self.workspace_root:
                        path_display = str(relative_path)
                    else:
                        path_display = str(path)

                    # Check if file name matches query
                    if any(w in path_display.lower() for w in query_words):
                        matched_files.append(f"- [File] {path_display}")
                        continue

                    # Check text content of code, markdown, and PDF files
                    if path.suffix in (".py", ".md", ".txt", ".toml", ".pdf") and path.stat().st_size < 5_000_000:
                        try:
                            if path.suffix == ".pdf":
                                import fitz  # PyMuPDF
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

        if not matched_files:
            return f"FileSearchAgent: Searched {file_count} files across paths but found no matches for: {', '.join(query_words)}"

        results_str = "\n".join(matched_files[:10])
        total_matches = len(matched_files)
        suffix = f"\n... and {total_matches - 10} more files." if total_matches > 10 else ""
        return f"FileSearchAgent found {total_matches} matches:\n{results_str}{suffix}"
