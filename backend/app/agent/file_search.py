from pathlib import Path
from typing import List


class FileSearchAgent:
    """
    Agent for searching local file system contents and list of files.
    """

    def __init__(self, workspace_root: str = "/home/krishna/Desktop/AI Engineering Workspace"):
        self.workspace_root = Path(workspace_root)

    def search(self, query: str) -> str:
        """
        Search files in the workspace for query keywords.
        """
        query_words = [w.lower() for w in query.split() if len(w) > 3]
        if not query_words:
            return "FileSearchAgent: Query is too short or generic. Please provide specific keywords."

        matched_files: List[str] = []
        file_count = 0

        # Scan for matching files in the workspace
        for path in self.workspace_root.rglob("*"):
            if path.is_file():
                # Skip build, cache and virtual environment directories
                parts = path.relative_to(self.workspace_root).parts
                if any(p.startswith(".") or p in ("venv", "node_modules", "__pycache__") for p in parts):
                    continue

                file_count += 1
                path_str = str(path.relative_to(self.workspace_root))
                # Check if file name matches query
                if any(w in path_str.lower() for w in query_words):
                    matched_files.append(f"- [File] {path_str}")
                    continue

                # Check text content of code and markdown files
                if path.suffix in (".py", ".md", ".txt", ".toml") and path.stat().st_size < 100_000:
                    try:
                        content = path.read_text(encoding="utf-8", errors="ignore")
                        if any(w in content.lower() for w in query_words):
                            matched_files.append(f"- [Content Match] {path_str}")
                    except Exception:
                        pass

        if not matched_files:
            return f"FileSearchAgent: Searched {file_count} files but found no matches for: {', '.join(query_words)}"

        results_str = "\n".join(matched_files[:10])
        total_matches = len(matched_files)
        suffix = f"\n... and {total_matches - 10} more files." if total_matches > 10 else ""
        return f"FileSearchAgent found {total_matches} matches in the workspace:\n{results_str}{suffix}"
