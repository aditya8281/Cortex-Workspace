from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.app.core.paths import PROJECT_ROOT


@dataclass(frozen=True)
class EntryPoint:
    path: str
    role: str


class WorkspaceIntelligenceService:
    def __init__(self, root: str | Path = PROJECT_ROOT):
        self.root = Path(root).resolve()

    def build_report(self) -> dict[str, Any]:
        files = self._gather_files()
        package_json = self._read_json(self.root / "frontend" / "package.json")
        pyproject = self._read_toml(self.root / "pyproject.toml")
        readme = self._read_text(self.root / "README.md")
        project_context = self._read_text(self.root / "Development guide" / "PROJECT_CONTEXT.md")

        dependencies = self._collect_dependencies(package_json, pyproject)
        frameworks = self._detect_frameworks(files, package_json, pyproject)
        entrypoints = self._detect_entrypoints(files)
        api_surface = self._detect_api_surface(files)
        build_process = self._detect_build_process(package_json)
        config = self._detect_config(files)
        execution_flow = self._detect_execution_flow()
        purpose = self._derive_purpose(readme, project_context, frameworks, dependencies)
        warnings = self._detect_warnings(files)

        return {
            "project_name": self.root.name,
            "purpose": purpose,
            "architecture": [
                "FastAPI backend with layered services, routers, AI gateway, executor, and replay store.",
                "React + Vite frontend that surfaces chat, execution traces, models, and admin tooling.",
                "RAG and memory subsystems support repo-aware and conversation-aware assistance.",
            ],
            "dependencies": dependencies,
            "frameworks": frameworks,
            "entrypoints": [entry.__dict__ for entry in entrypoints],
            "apis": api_surface,
            "execution_flow": execution_flow,
            "config": config,
            "build_process": build_process,
            "key_files": self._key_files(files),
            "warnings": warnings,
            "evidence": self._evidence_snippets(files),
        }

    def _gather_files(self) -> list[Path]:
        patterns = [
            "backend/app/main.py",
            "backend/app/api/router.py",
            "backend/app/api/v1/*.py",
            "backend/app/executor/*.py",
            "backend/app/rag/*.py",
            "backend/app/ai/**/*.py",
            "backend/app/agent/*.py",
            "backend/app/tools/*.py",
            "frontend/src/*.tsx",
            "frontend/src/*.ts",
            "frontend/package.json",
            "frontend/vite.config.ts",
            "pyproject.toml",
            "README.md",
            "Makefile",
        ]

        files: list[Path] = []
        seen: set[Path] = set()
        for pattern in patterns:
            for path in self.root.glob(pattern):
                resolved = path.resolve()
                if resolved in seen or not resolved.is_file():
                    continue
                seen.add(resolved)
                files.append(resolved)
        return files

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
            return json.loads(self._read_text(path, limit=20000))  # type: ignore[return-value]
        except Exception:
            return {}

    def _read_toml(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        try:
            return tomllib.loads(self._read_text(path, limit=20000))
        except Exception:
            return {}

    def _collect_dependencies(self, package_json: dict[str, Any], pyproject: dict[str, Any]) -> list[str]:
        deps: list[str] = []

        def add(item: str) -> None:
            if item and item not in deps:
                deps.append(item)

        for name in package_json.get("dependencies", {}):
            add(f"frontend:{name}")

        project = pyproject.get("project", {})
        for name in project.get("dependencies", []):
            add(f"backend:{name}")

        return deps[:24]

    def _detect_frameworks(
        self,
        files: list[Path],
        package_json: dict[str, Any],
        pyproject: dict[str, Any],
    ) -> list[str]:
        frameworks: list[str] = []

        def add(name: str) -> None:
            if name not in frameworks:
                frameworks.append(name)

        deps = {
            *(package_json.get("dependencies", {}) or {}),
            *((pyproject.get("project", {}) or {}).get("dependencies", []) or []),
        }

        if any(dep.startswith("react") for dep in deps) or any(path.name.endswith(".tsx") for path in files):
            add("React")
        if "vite" in deps or (self.root / "frontend" / "vite.config.ts").exists():
            add("Vite")
        if any("fastapi" in dep.lower() for dep in deps) or (self.root / "backend" / "app" / "main.py").exists():
            add("FastAPI")
        if any("sqlalchemy" in dep.lower() for dep in deps):
            add("SQLAlchemy")
        if any("faiss" in dep.lower() for dep in deps):
            add("FAISS")
        if any("sentence-transformers" in dep.lower() for dep in deps):
            add("Sentence Transformers")
        if any("pymupdf" in dep.lower() for dep in deps):
            add("PyMuPDF")

        return frameworks

    def _detect_entrypoints(self, files: list[Path]) -> list[EntryPoint]:
        entrypoints: list[EntryPoint] = []

        def add(path: Path, role: str) -> None:
            if path.exists():
                entrypoints.append(EntryPoint(path=str(path.relative_to(self.root)), role=role))

        add(self.root / "backend" / "app" / "main.py", "FastAPI application entrypoint")
        add(self.root / "frontend" / "src" / "main.tsx", "React application bootstrap")
        add(self.root / "frontend" / "vite.config.ts", "Vite build configuration")
        add(self.root / "scripts" / "rebuild_index.py", "RAG index rebuild utility")
        add(self.root / "Makefile", "Local development command surface")

        return entrypoints

    def _detect_api_surface(self, files: list[Path]) -> list[str]:
        api_lines: list[str] = []
        route_pattern = re.compile(r'@router\.(get|post|put|delete|patch)\(([^)]*)\)')

        for path in files:
            if "backend/app/api/v1" not in str(path):
                continue

            text = self._read_text(path, limit=12000)
            for match in route_pattern.finditer(text):
                method = match.group(1).upper()
                raw_path = match.group(2)
                cleaned = raw_path.split(",")[0].strip().strip('"\'')
                api_lines.append(f"{method} {cleaned or '/'} -> {path.relative_to(self.root)}")

        return api_lines[:40]

    def _detect_build_process(self, package_json: dict[str, Any]) -> list[str]:
        process: list[str] = []
        scripts = package_json.get("scripts", {})
        if scripts:
            process.append("Frontend scripts:")
            for name, command in scripts.items():
                process.append(f"- {name}: {command}")

        makefile = self.root / "Makefile"
        if makefile.exists():
            process.append("Backend automation: `make dev`, `make lint`, `make test`, `make migrate`, `make format`.")

        if (self.root / "backend" / "app" / "main.py").exists():
            process.append("Backend starts with `backend.app.main:app` via Uvicorn.")

        return process

    def _detect_config(self, files: list[Path]) -> list[str]:
        config: list[str] = []
        candidates = [
            self.root / "backend" / "app" / "core" / "config.py",
            self.root / "frontend" / "vite.config.ts",
            self.root / "frontend" / "package.json",
            self.root / "pyproject.toml",
            self.root / ".env",
        ]

        for path in candidates:
            if path.exists():
                config.append(str(path.relative_to(self.root)))

        return config

    def _detect_execution_flow(self) -> list[str]:
        flow = [
            "API request enters FastAPI router.",
            "AIGateway normalizes model/provider settings.",
            "AIExecutor classifies intent and builds the execution graph.",
            "GraphRunner executes memory, tools, and LLM synthesis steps.",
            "ToolRegistry routes to file search, system scan, and RAG.",
            "Execution state is persisted for replay and debugging.",
            "ResponseBuilder returns the final assistant answer and execution_id.",
        ]
        return flow

    def _derive_purpose(
        self,
        readme: str,
        project_context: str,
        frameworks: list[str],
        dependencies: list[str],
    ) -> str:
        if "local-first AI operating system" in project_context:
            return (
                "Cortex Workspace is a local-first AI operating system and engineering console "
                "that blends chat, file intelligence, RAG, execution replay, and model routing."
            )
        if "React" in frameworks and dependencies:
            return "A full-stack workspace for local AI chat, repository awareness, and execution telemetry."
        if readme:
            first_line = readme.strip().splitlines()[0]
            return first_line[:240]
        return "A local-first AI workspace with chat, memory, and repo intelligence."

    def _detect_warnings(self, files: list[Path]) -> list[str]:
        warnings: list[str] = []
        if not (self.root / ".env").exists():
            warnings.append("No .env file found at the workspace root.")
        if not (self.root / "frontend" / "src" / "App.tsx").exists():
            warnings.append("Frontend app entrypoint is missing or relocated.")
        if not any("main.py" in str(path) for path in files):
            warnings.append("FastAPI entrypoint was not detected in the scan.")
        return warnings

    def _key_files(self, files: list[Path]) -> list[str]:
        wanted = [
            "backend/app/main.py",
            "backend/app/api/router.py",
            "backend/app/executor/executor.py",
            "backend/app/executor/graph_runner.py",
            "backend/app/rag/service.py",
            "backend/app/ai/gateway.py",
            "frontend/src/App.tsx",
            "frontend/src/api/ai.ts",
            "frontend/src/api/execution.ts",
        ]
        return [str(path.relative_to(self.root)) for path in files if str(path.relative_to(self.root)) in wanted]

    def _evidence_snippets(self, files: list[Path]) -> list[dict[str, str]]:
        evidence: list[dict[str, str]] = []
        for rel in [
            self.root / "backend" / "app" / "main.py",
            self.root / "backend" / "app" / "api" / "router.py",
            self.root / "backend" / "app" / "executor" / "executor.py",
            self.root / "backend" / "app" / "rag" / "service.py",
            self.root / "frontend" / "src" / "App.tsx",
        ]:
            if not rel.exists():
                continue
            text = self._read_text(rel, limit=2200)
            snippet = text.strip().splitlines()[:10]
            evidence.append(
                {
                    "path": str(rel.relative_to(self.root)),
                    "snippet": "\n".join(snippet),
                }
            )
        return evidence
