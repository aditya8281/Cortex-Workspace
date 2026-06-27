"""Repository scanner — analyzes repo structure, languages, frameworks, dependencies."""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime

from sqlalchemy.orm import Session

from backend.app.models.awareness.repo_analyzer import RepositoryIndex

# Language detection by file extension
EXTENSION_TO_LANGUAGE: dict[str, str] = {
    ".py": "python",
    ".pyx": "python",
    ".pyi": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".rs": "rust",
    ".go": "go",
    ".java": "java",
    ".rb": "ruby",
    ".php": "php",
    ".c": "c",
    ".h": "c_header",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
    ".lua": "lua",
    ".sh": "shell",
    ".bash": "shell",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".xml": "xml",
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".scss": "scss",
    ".md": "markdown",
    ".rst": "restructuredtext",
    ".sql": "sql",
    ".toml": "toml",
    ".ini": "ini",
}

# Framework detection by config file presence
FRAMEWORK_INDICATORS: dict[str, str] = {
    "next.config.js": "next.js",
    "next.config.mjs": "next.js",
    "next.config.ts": "next.js",
    "nuxt.config.js": "nuxt",
    "nuxt.config.ts": "nuxt",
    "vite.config.js": "vite",
    "vite.config.ts": "vite",
    "angular.json": "angular",
    "svelte.config.js": "svelte",
    "svelte.config.ts": "svelte",
    "manage.py": "django",
    "wsgi.py": "django",
    "asgi.py": "fastapi",
    "pyproject.toml": "python",
    "setup.py": "python",
    "setup.cfg": "python",
    "Cargo.toml": "rust",
    "go.mod": "go",
    "Gemfile": "ruby",
    "Rakefile": "ruby",
    "pom.xml": "java",
    "build.gradle": "java",
    "build.gradle.kts": "java",
    "composer.json": "php",
    "CMakeLists.txt": "cmake",
    "Makefile": "make",
}

# Directories to skip
SKIP_DIRS: set[str] = {
    ".git",
    "node_modules",
    "__pycache__",
    "venv",
    ".venv",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "target",
    ".idea",
    ".vscode",
}


class RepositoryScannerService:
    """Analyzes repository structure: languages, framework, dependencies, stats."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def scan_repository(
        self,
        user_id: int,
        repo_path: str,
    ) -> RepositoryIndex:
        """Scan *repo_path* and create/update a RepositoryIndex record."""
        languages = self._detect_languages(repo_path)
        framework = self._detect_framework(repo_path)
        dependencies = self._detect_dependencies(repo_path)
        total_files, total_lines = self._count_files(repo_path)
        git_branch, last_commit = self._get_git_info(repo_path)

        existing = (
            self.db.query(RepositoryIndex)
            .filter(
                RepositoryIndex.user_id == user_id,
                RepositoryIndex.repo_path == repo_path,
            )
            .first()
        )

        if existing is not None:
            existing.languages = json.dumps(languages)
            existing.total_files = total_files
            existing.total_lines = total_lines
            existing.framework = framework
            existing.dependencies = json.dumps(dependencies)
            existing.git_branch = git_branch
            existing.last_commit_hash = last_commit
            existing.last_indexed = datetime.now()
            self.db.commit()
            self.db.refresh(existing)
            return existing

        repo_index = RepositoryIndex(
            user_id=user_id,
            repo_path=repo_path,
            repo_name=os.path.basename(repo_path),
            languages=json.dumps(languages),
            total_files=total_files,
            total_lines=total_lines,
            framework=framework,
            dependencies=json.dumps(dependencies),
            git_branch=git_branch,
            last_commit_hash=last_commit,
            last_indexed=datetime.now(),
        )
        self.db.add(repo_index)
        self.db.commit()
        self.db.refresh(repo_index)
        return repo_index

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _detect_languages(self, repo_path: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for _root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for fname in files:
                ext = os.path.splitext(fname)[1].lower()
                lang = EXTENSION_TO_LANGUAGE.get(ext)
                if lang:
                    counts[lang] = counts.get(lang, 0) + 1
        return counts

    def _detect_framework(self, repo_path: str) -> str | None:
        for filename, framework in FRAMEWORK_INDICATORS.items():
            if os.path.exists(os.path.join(repo_path, filename)):
                return framework
        return None

    def _detect_dependencies(self, repo_path: str) -> list[str]:
        deps: list[str] = []

        # Python: requirements.txt
        req_file = os.path.join(repo_path, "requirements.txt")
        if os.path.exists(req_file):
            try:
                with open(req_file) as fh:
                    for line in fh:
                        line = line.strip()
                        if line and not line.startswith("#") and not line.startswith("-"):
                            deps.append(
                                line.split("==")[0].split(">=")[0].split("<=")[0].strip()
                            )
            except OSError:
                pass

        # Node: package.json
        pkg_file = os.path.join(repo_path, "package.json")
        if os.path.exists(pkg_file):
            try:
                with open(pkg_file) as fh:
                    pkg = json.load(fh)
                    deps.extend(list(pkg.get("dependencies", {}).keys()))
                    deps.extend(list(pkg.get("devDependencies", {}).keys()))
            except (json.JSONDecodeError, KeyError, OSError):
                pass

        # Rust: Cargo.toml
        cargo_file = os.path.join(repo_path, "Cargo.toml")
        if os.path.exists(cargo_file):
            try:
                with open(cargo_file) as fh:
                    in_deps = False
                    for line in fh:
                        line = line.strip()
                        if line == "[dependencies]":
                            in_deps = True
                        elif line.startswith("["):
                            in_deps = False
                        elif in_deps and "=" in line:
                            dep_name = line.split("=")[0].strip()
                            if dep_name:
                                deps.append(dep_name)
            except OSError:
                pass

        return deps[:100]

    def _count_files(self, repo_path: str) -> tuple[int, int]:
        total_files = 0
        total_lines = 0
        for _root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for fname in files:
                total_files += 1
                filepath = os.path.join(_root, fname)
                try:
                    with open(filepath, errors="ignore") as fh:
                        total_lines += sum(1 for _ in fh)
                except (OSError, UnicodeDecodeError, PermissionError):
                    pass
        return total_files, total_lines

    def _get_git_info(self, repo_path: str) -> tuple[str | None, str | None]:
        try:
            branch_result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=5,
            )
            commit_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=5,
            )
            branch = branch_result.stdout.strip() or None
            commit = commit_result.stdout.strip() or None
            return branch, commit
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return None, None
