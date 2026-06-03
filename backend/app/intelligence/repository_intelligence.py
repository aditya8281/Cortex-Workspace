"""Generate and persist repository intelligence profiles."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from backend.app.intelligence.models import KnowledgeEntry, RepositoryProfile


class RepositoryIntelligenceService:
    def analyze(self, repo_path: Path) -> dict[str, Any]:
        repo_path = repo_path.resolve()
        name = repo_path.name
        readme = self._read_text(repo_path / "README.md", 8000)
        pyproject = self._read_toml(repo_path / "pyproject.toml")
        package_json = self._read_json(repo_path / "frontend" / "package.json") or self._read_json(
            repo_path / "package.json"
        )

        dependencies = self._collect_dependencies(pyproject, package_json)
        tech_stack = self._detect_tech_stack(repo_path, pyproject, package_json)
        entry_points = self._detect_entry_points(repo_path)
        important_files = self._important_files(repo_path)
        architecture = self._architecture_summary(repo_path, tech_stack, entry_points)
        summary = self._build_summary(name, readme, tech_stack, dependencies)

        return {
            "path": str(repo_path),
            "name": name,
            "summary": summary,
            "architecture_summary": architecture,
            "tech_stack": ", ".join(tech_stack),
            "dependencies": dependencies,
            "entry_points": entry_points,
            "important_files": important_files,
        }

    def upsert_profile(
        self, db: Session, profile: dict[str, Any], user_id: int | None = None
    ) -> RepositoryProfile:
        path = profile["path"]
        existing = db.query(RepositoryProfile).filter(RepositoryProfile.path == path).first()
        if existing is None:
            existing = RepositoryProfile(path=path, name=profile["name"], user_id=user_id)
            db.add(existing)

        existing.name = profile["name"]
        existing.summary = profile["summary"]
        existing.architecture_summary = profile["architecture_summary"]
        existing.tech_stack = profile["tech_stack"]
        existing.dependencies_json = json.dumps(profile.get("dependencies", []))
        existing.entry_points_json = json.dumps(profile.get("entry_points", []))
        existing.important_files_json = json.dumps(profile.get("important_files", []))
        if user_id is not None:
            existing.user_id = user_id

        db.flush()
        return existing

    def store_searchable_memory(
        self, db: Session, profile: dict[str, Any], user_id: int | None = None
    ) -> KnowledgeEntry:
        source_key = f"repo:{profile['path']}"
        existing = (
            db.query(KnowledgeEntry)
            .filter(KnowledgeEntry.source_key == source_key)
            .first()
        )
        content = (
            f"Repository: {profile['name']}\n"
            f"Path: {profile['path']}\n"
            f"Summary: {profile['summary']}\n"
            f"Architecture: {profile['architecture_summary']}\n"
            f"Tech stack: {profile['tech_stack']}\n"
            f"Dependencies: {', '.join(profile.get('dependencies', [])[:30])}\n"
            f"Entry points: {', '.join(profile.get('entry_points', [])[:20])}"
        )
        if existing is None:
            existing = KnowledgeEntry(
                category="repository",
                title=f"Repository: {profile['name']}",
                content=content,
                source_path=profile["path"],
                source_key=source_key,
                user_id=user_id,
            )
            db.add(existing)
        else:
            existing.content = content
            existing.title = f"Repository: {profile['name']}"

        db.flush()
        return existing

    def _read_text(self, path: Path, limit: int = 6000) -> str:
        if not path.exists():
            return ""
        try:
            return path.read_text(encoding="utf-8", errors="ignore")[:limit]
        except Exception:
            return ""

    def _read_json(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        try:
            return json.loads(self._read_text(path, 20000))
        except Exception:
            return {}

    def _read_toml(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        try:
            return tomllib.loads(self._read_text(path, 20000))
        except Exception:
            return {}

    def _collect_dependencies(
        self, pyproject: dict[str, Any], package_json: dict[str, Any]
    ) -> list[str]:
        deps: list[str] = []
        project_deps = pyproject.get("project", {}).get("dependencies", [])
        if isinstance(project_deps, list):
            deps.extend(str(d) for d in project_deps)
        for section in ("dependencies", "devDependencies"):
            block = package_json.get(section, {})
            if isinstance(block, dict):
                deps.extend(f"{name}@{version}" for name, version in block.items())
        return sorted(set(deps))[:80]

    def _detect_tech_stack(
        self, repo_path: Path, pyproject: dict[str, Any], package_json: dict[str, Any]
    ) -> list[str]:
        stack: list[str] = []
        if pyproject:
            stack.append("Python")
        if package_json:
            stack.append("JavaScript/TypeScript")
        if (repo_path / "backend" / "app" / "main.py").exists():
            stack.append("FastAPI")
        if (repo_path / "frontend" / "vite.config.ts").exists() or (
            repo_path / "vite.config.ts"
        ).exists():
            stack.append("Vite")
        if (repo_path / "docker-compose.yml").exists():
            stack.append("Docker")
        if (repo_path / "Cargo.toml").exists():
            stack.append("Rust")
        if (repo_path / "go.mod").exists():
            stack.append("Go")
        return sorted(set(stack))

    def _detect_entry_points(self, repo_path: Path) -> list[str]:
        candidates = [
            "backend/app/main.py",
            "app/main.py",
            "src/main.py",
            "main.py",
            "frontend/src/main.tsx",
            "src/index.ts",
        ]
        found: list[str] = []
        for rel in candidates:
            if (repo_path / rel).exists():
                found.append(rel)
        return found

    def _important_files(self, repo_path: Path) -> list[str]:
        names = [
            "README.md",
            "pyproject.toml",
            "package.json",
            "docker-compose.yml",
            "Makefile",
            ".env.example",
        ]
        return [n for n in names if (repo_path / n).exists()]

    def _architecture_summary(
        self, repo_path: Path, tech_stack: list[str], entry_points: list[str]
    ) -> str:
        parts = [f"Project at {repo_path}."]
        if tech_stack:
            parts.append(f"Technologies: {', '.join(tech_stack)}.")
        if entry_points:
            parts.append(f"Entry points: {', '.join(entry_points)}.")
        if (repo_path / "backend").exists() and (repo_path / "frontend").exists():
            parts.append("Split backend/frontend layout detected.")
        return " ".join(parts)

    def _build_summary(
        self, name: str, readme: str, tech_stack: list[str], dependencies: list[str]
    ) -> str:
        intro = ""
        if readme:
            for line in readme.splitlines():
                cleaned = line.strip()
                if len(cleaned) > 40 and not cleaned.startswith("#"):
                    intro = cleaned[:400]
                    break
            if not intro:
                intro = readme.splitlines()[0][:400] if readme.splitlines() else ""
        stack_part = f" Stack: {', '.join(tech_stack)}." if tech_stack else ""
        dep_part = f" Key dependencies: {', '.join(dependencies[:8])}." if dependencies else ""
        return f"{name}: {intro or 'Local repository discovered by Cortex.'}{stack_part}{dep_part}".strip()
