"""IndexingRules — determines which files should be indexed."""

from __future__ import annotations

import fnmatch
import os
from pathlib import Path

from backend.app.models.indexing_config import IndexingConfig
from backend.app.services.chunker import SKIP_DIRS

# Default exclusion rules — things that should NEVER be indexed
DEFAULT_EXCLUSIONS: dict[str, set[str] | list[str] | int] = {
    "directories": SKIP_DIRS
    | {
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".venv",
        "env",
        ".env",
        ".cache",
        "coverage",
        ".coverage",
        "htmlcov",
        "vendor",
        ".bundle",
        "tmp",
        ".tmp",
        ".DS_Store",
        "Thumbs.db",
        ".svn",
        ".hg",
        "logs",
        "dist",
        "build",
        ".next",
        ".nuxt",
    },
    "patterns": [
        "*.min.js",
        "*.min.css",
        "*.map",
        "*.pyc",
        "*.pyo",
        "*.so",
        "*.dylib",
        "*.dll",
        "*.exe",
        "*.bin",
        "*.jpg",
        "*.jpeg",
        "*.png",
        "*.gif",
        "*.bmp",
        "*.ico",
        "*.svg",
        "*.mp3",
        "*.mp4",
        "*.wav",
        "*.avi",
        "*.mov",
        "*.zip",
        "*.tar",
        "*.gz",
        "*.rar",
        "*.7z",
        "*.pdf",
        "*.doc",
        "*.docx",
        "*.xls",
        "*.xlsx",
        "*.lock",
        "*.sum",
        "package-lock.json",
        "yarn.lock",
        ".env.*",
        "*.log",
        "*.tmp",
        "*.temp",
    ],
    "max_size_bytes": 1_000_000,
}


class IndexingRules:
    """Determines which files should be indexed."""

    def __init__(self, config: IndexingConfig | None = None):
        self._config = config

    def should_index(self, file_path: str, base_dir: str) -> bool:
        """Check if a file should be indexed."""
        rel_path = os.path.relpath(file_path, base_dir)
        parts = Path(rel_path).parts

        if self._is_excluded_directory(parts):
            return False

        if self._is_excluded_pattern(os.path.basename(file_path)):
            return False

        try:
            size = os.path.getsize(file_path)
            max_size = self._config.max_file_size_bytes if self._config else DEFAULT_EXCLUSIONS["max_size_bytes"]
            if size > max_size:
                return False
        except OSError:
            return False

        if (
            self._config
            and self._config.include_paths
            and not any(rel_path.startswith(p) for p in self._config.include_paths)
        ):
            return False

        if (
            self._config
            and self._config.exclude_paths
            and any(rel_path.startswith(p) for p in self._config.exclude_paths)
        ):
            return False

        if (
            self._config
            and self._config.include_patterns
            and not any(fnmatch.fnmatch(file_path, p) for p in self._config.include_patterns)
        ):
            return False

        return not (
            self._config
            and self._config.exclude_patterns
            and any(fnmatch.fnmatch(file_path, p) for p in self._config.exclude_patterns)
        )

    def _is_excluded_directory(self, parts: tuple[str, ...]) -> bool:
        excluded = DEFAULT_EXCLUSIONS["directories"]
        if self._config and self._config.exclude_paths:
            excluded = excluded | set(self._config.exclude_paths)
        return any(part in excluded or part.endswith(".egg-info") for part in parts[:-1])

    def _is_excluded_pattern(self, filename: str) -> bool:
        patterns = DEFAULT_EXCLUSIONS["patterns"]
        if self._config and self._config.exclude_patterns:
            patterns = patterns + self._config.exclude_patterns
        return any(fnmatch.fnmatch(filename, p) for p in patterns)

    def get_stats(self, base_dir: str) -> dict:
        """Scan directory and return indexing stats without actually indexing."""
        total = 0
        included = 0
        excluded_by_size = 0
        excluded_by_pattern = 0
        excluded_by_directory = 0

        for root, _dirs, files in os.walk(base_dir):
            for f in files:
                total += 1
                fp = os.path.join(root, f)
                rel = os.path.relpath(fp, base_dir)
                parts = Path(rel).parts

                if self._is_excluded_directory(parts):
                    excluded_by_directory += 1
                    continue
                if self._is_excluded_pattern(f):
                    excluded_by_pattern += 1
                    continue
                try:
                    if os.path.getsize(fp) > (
                        self._config.max_file_size_bytes if self._config else DEFAULT_EXCLUSIONS["max_size_bytes"]
                    ):
                        excluded_by_size += 1
                        continue
                except OSError:
                    continue
                included += 1

        return {
            "total_files": total,
            "will_index": included,
            "excluded_by_directory": excluded_by_directory,
            "excluded_by_pattern": excluded_by_pattern,
            "excluded_by_size": excluded_by_size,
        }
