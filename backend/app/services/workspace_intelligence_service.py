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


@dataclass(frozen=True)
class ActivityFeedItem:
    title: str
    detail: str
    tone: str
    count: int | None = None


@dataclass(frozen=True)
class RelationshipEdge:
    source: str
    target: str
    relation: str


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
        query_classes = self._detect_query_classes()
        purpose = self._derive_purpose(readme, project_context, frameworks, dependencies)
        warnings = self._detect_warnings(files)
        repositories = self._detect_repositories()
        concepts = self._detect_concepts(files, frameworks, dependencies, readme, project_context)
        activity_feed = self._build_activity_feed(files, repositories, concepts, warnings)
        repository_model = self._build_repository_model(files, dependencies, config, entrypoints, api_surface)
        system_access = self._build_system_access()
        dependency_graph = self._build_dependency_graph(dependencies, frameworks)
        module_graph = self._build_module_graph(files)
        knowledge_graph = self._build_knowledge_graph(concepts, repository_model["relationships"])
        memory_summary = self._build_memory_summary(project_context, warnings, concepts)

        return {
            "project_name": self.root.name,
            "purpose": purpose,
            "architecture": [
                "FastAPI backend with layered services, routers, AI gateway, executor, and replay store.",
                "React + Vite frontend that surfaces chat, execution traces, models, and admin tooling.",
                "RAG and memory subsystems support repo-aware and conversation-aware assistance.",
            ],
            "repositories": repositories,
            "concepts": concepts,
            "repository_model": repository_model,
            "system_access": system_access,
            "dependency_graph": dependency_graph,
            "module_graph": module_graph,
            "knowledge_graph": knowledge_graph,
            "query_classes": query_classes,
            "memory_summary": memory_summary,
            "dependencies": dependencies,
            "frameworks": frameworks,
            "entrypoints": [entry.__dict__ for entry in entrypoints],
            "apis": api_surface,
            "execution_flow": execution_flow,
            "config": config,
            "build_process": build_process,
            "key_files": self._key_files(files),
            "warnings": warnings,
            "activity_feed": [item.__dict__ for item in activity_feed],
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

    def _detect_repositories(self) -> list[str]:
        repositories: list[str] = []

        def add(label: str, path: Path) -> None:
            if path.exists() and label not in repositories:
                repositories.append(label)

        add("Workspace root", self.root / "pyproject.toml")
        add("Backend API", self.root / "backend" / "app" / "main.py")
        add("Frontend app", self.root / "frontend" / "package.json")

        return repositories

    def _detect_concepts(
        self,
        files: list[Path],
        frameworks: list[str],
        dependencies: list[str],
        readme: str,
        project_context: str,
    ) -> list[str]:
        concepts: list[str] = []

        def add(name: str, condition: bool = True) -> None:
            if condition and name not in concepts:
                concepts.append(name)

        source_text = "\n".join([readme, project_context]).lower()
        dependency_text = " ".join([*dependencies, *frameworks]).lower()
        file_text = " ".join(str(path.relative_to(self.root)).lower() for path in files)

        add("Local-first workspace", "local-first" in source_text)
        add("React UI", "react" in dependency_text or any(path.name.endswith(".tsx") for path in files))
        add("FastAPI services", "fastapi" in dependency_text or (self.root / "backend" / "app" / "main.py").exists())
        add("Vite tooling", "vite" in dependency_text or (self.root / "frontend" / "vite.config.ts").exists())
        add("Repository awareness", "rag" in file_text or "repository" in source_text)
        add("Execution replay", "execution" in file_text or (self.root / "backend" / "app" / "executor" / "execution_replay.py").exists())
        add("Model routing", "gateway" in file_text or (self.root / "backend" / "app" / "ai" / "gateway.py").exists())
        add("Memory layer", "memory" in file_text or (self.root / "backend" / "app" / "ai" / "memory").exists())
        add("RAG retrieval", (self.root / "backend" / "app" / "rag" / "service.py").exists())
        add("Authentication", "auth" in file_text or (self.root / "frontend" / "src" / "api" / "auth.ts").exists())
        add("Admin tools", "admin" in file_text or (self.root / "frontend" / "src" / "App.tsx").exists())
        add("Workspace intelligence", (self.root / "backend" / "app" / "services" / "workspace_intelligence_service.py").exists())

        return concepts[:12]

    def _build_repository_model(
        self,
        files: list[Path],
        dependencies: list[str],
        config: list[str],
        entrypoints: list[EntryPoint],
        api_surface: list[str],
    ) -> dict[str, Any]:
        python_symbols = self._collect_python_symbols(files)
        ts_symbols = self._collect_typescript_symbols(files)
        docs = [name for name in ["README.md", "Development guide/PROJECT_CONTEXT.md"] if (self.root / name).exists()]
        relationships = self._collect_relationships(entrypoints, api_surface, python_symbols, ts_symbols)

        return {
            "modules": self._collect_module_names(files),
            "files": self._key_files(files),
            "classes": python_symbols["classes"],
            "functions": python_symbols["functions"] + ts_symbols["functions"],
            "apis": api_surface,
            "configurations": config,
            "dependencies": dependencies,
            "entry_points": [entry.path for entry in entrypoints],
            "documentation": docs,
            "relationships": [edge.__dict__ for edge in relationships[:24]],
        }

    def _collect_module_names(self, files: list[Path]) -> list[str]:
        modules: list[str] = []

        def add(value: str) -> None:
            if value and value not in modules:
                modules.append(value)

        for path in files:
            rel = path.relative_to(self.root)
            parts = rel.parts
            if not parts:
                continue
            if parts[0] in {"backend", "frontend"} and len(parts) > 2:
                add(".".join(parts[:3]))
            elif parts[0] in {"backend", "frontend"} and len(parts) > 1:
                add(".".join(parts[:2]))

        return modules[:20]

    def _collect_python_symbols(self, files: list[Path]) -> dict[str, list[str]]:
        classes: list[str] = []
        functions: list[str] = []
        class_pattern = re.compile(r"^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)", re.MULTILINE)
        def_pattern = re.compile(r"^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)", re.MULTILINE)

        for path in files:
            if path.suffix != ".py":
                continue
            text = self._read_text(path, limit=20000)
            for match in class_pattern.findall(text):
                if match not in classes:
                    classes.append(match)
            for match in def_pattern.findall(text):
                if match not in functions:
                    functions.append(match)

        return {"classes": classes[:20], "functions": functions[:24]}

    def _collect_typescript_symbols(self, files: list[Path]) -> dict[str, list[str]]:
        functions: list[str] = []
        patterns = [
            re.compile(r"export\s+function\s+([A-Za-z_][A-Za-z0-9_]*)"),
            re.compile(r"const\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\([^)]*\)\s*=>"),
            re.compile(r"function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\("),
        ]

        for path in files:
            if path.suffix not in {".ts", ".tsx"}:
                continue
            text = self._read_text(path, limit=20000)
            for pattern in patterns:
                for match in pattern.findall(text):
                    if match not in functions:
                        functions.append(match)

        return {"functions": functions[:24]}

    def _collect_relationships(
        self,
        entrypoints: list[EntryPoint],
        api_surface: list[str],
        python_symbols: dict[str, list[str]],
        ts_symbols: dict[str, list[str]],
    ) -> list[RelationshipEdge]:
        relationships: list[RelationshipEdge] = []

        def add(source: str, target: str, relation: str) -> None:
            edge = RelationshipEdge(source=source, target=target, relation=relation)
            if edge not in relationships:
                relationships.append(edge)

        for entry in entrypoints:
            add(entry.path, entry.role, "entrypoint")

        for api in api_surface[:12]:
            add("backend/app/api", api, "exposes")

        for name in python_symbols["classes"][:10]:
            add("python classes", name, "contains")

        for name in python_symbols["functions"][:10]:
            add("python functions", name, "contains")

        for name in ts_symbols["functions"][:10]:
            add("frontend functions", name, "contains")

        return relationships

    def _build_dependency_graph(self, dependencies: list[str], frameworks: list[str]) -> dict[str, Any]:
        nodes: list[str] = ["workspace"]
        nodes.extend([item for item in ["backend", "frontend", *frameworks] if item not in nodes])
        for dep in dependencies[:14]:
            if dep not in nodes:
                nodes.append(dep)

        edges = [
            {"source": "workspace", "target": "backend", "relation": "contains"},
            {"source": "workspace", "target": "frontend", "relation": "contains"},
        ]
        if "React" in frameworks:
            edges.append({"source": "frontend", "target": "React", "relation": "uses"})
        if "Vite" in frameworks:
            edges.append({"source": "frontend", "target": "Vite", "relation": "builds_with"})
        if "FastAPI" in frameworks:
            edges.append({"source": "backend", "target": "FastAPI", "relation": "serves_with"})

        for dep in dependencies[:8]:
            source = "frontend" if dep.startswith("frontend:") else "backend"
            edges.append({"source": source, "target": dep, "relation": "depends_on"})

        return {"nodes": nodes[:24], "edges": edges[:20]}

    def _build_module_graph(self, files: list[Path]) -> dict[str, Any]:
        nodes: list[str] = []
        edges: list[dict[str, str]] = []

        for path in files:
            rel = str(path.relative_to(self.root))
            if rel.startswith("backend/app"):
                module = ".".join(Path(rel).with_suffix("").parts)
                if module not in nodes:
                    nodes.append(module)
            if rel.startswith("frontend/src"):
                module = ".".join(Path(rel).with_suffix("").parts)
                if module not in nodes:
                    nodes.append(module)

        if "backend.app.main" in nodes:
            edges.append({"source": "backend.app.main", "target": "backend.app.api.router", "relation": "mounts"})
        if "frontend.src.App" in nodes:
            edges.append({"source": "frontend.src.App", "target": "frontend.src.api.ai", "relation": "imports"})
            edges.append({"source": "frontend.src.App", "target": "frontend.src.api.auth", "relation": "imports"})

        return {"nodes": nodes[:24], "edges": edges[:20]}

    def _build_knowledge_graph(self, concepts: list[str], relationships: list[dict[str, str]]) -> dict[str, Any]:
        nodes = concepts[:12]
        edges: list[dict[str, str]] = []

        for index in range(max(0, len(nodes) - 1)):
            edges.append({"source": nodes[index], "target": nodes[index + 1], "relation": "related_to"})

        if relationships:
            first = relationships[0]
            edges.append(
                {
                    "source": first["source"],
                    "target": first["target"],
                    "relation": first["relation"],
                }
            )

        return {"nodes": nodes, "edges": edges[:18]}

    def _detect_query_classes(self) -> list[dict[str, str]]:
        return [
            {
                "name": "SIMPLE",
                "retrieval": "Light semantic lookup",
                "use_case": "Explain a function, symbol, or file.",
            },
            {
                "name": "COMPLEX",
                "retrieval": "Broader graph expansion",
                "use_case": "Trace cross-module behavior or dependencies.",
            },
            {
                "name": "ARCHITECTURAL",
                "retrieval": "Architecture-first traversal",
                "use_case": "Reason about services, boundaries, and system shape.",
            },
            {
                "name": "DEBUGGING",
                "retrieval": "Causal chain + execution replay",
                "use_case": "Find a root cause and its dependency chain.",
            },
            {
                "name": "REFACTORING",
                "retrieval": "Symbol and call graph",
                "use_case": "Safely reshape code across files.",
            },
            {
                "name": "IMPLEMENTATION",
                "retrieval": "Relevant files + patterns + examples",
                "use_case": "Add a feature with repository context.",
            },
            {
                "name": "SECURITY",
                "retrieval": "Configuration, auth, and trust boundaries",
                "use_case": "Audit risk and exposure points.",
            },
            {
                "name": "PERFORMANCE",
                "retrieval": "Hot path + data flow",
                "use_case": "Track expensive execution paths.",
            },
        ]

    def _build_memory_summary(self, project_context: str, warnings: list[str], concepts: list[str]) -> dict[str, list[str]]:
        known_bugs = warnings[:4] if warnings else ["No obvious repository warnings found."]
        design_rationale = [
            "Keep the UI chat-first while surfacing repository intelligence on demand.",
            "Use structured panels for graphs, feeds, and configuration instead of raw dumps.",
            "Prefer local inference and repository context before expanding to broader reasoning.",
        ]
        patterns = concepts[:6] if concepts else ["Repository scan completed", "Graph expansion ready"]
        decisions = [
            "Workspace intelligence is assembled from code, docs, and config.",
            "Activity items are generated from repository-level signals, not empty placeholders.",
        ]
        if "local-first" in project_context.lower():
            decisions.append("Local-first execution stays the default operating mode.")
        return {
            "patterns": patterns,
            "decisions": decisions,
            "known_bugs": known_bugs,
            "design_rationale": design_rationale,
        }

    def _build_system_access(self) -> dict[str, Any]:
        home = Path.home().resolve()
        meaningful_roots = [
            self.root,
            home,
            home / "Desktop",
            home / "Documents",
            home / "Downloads",
            home / "Projects",
            home / "Work",
            home / "Development",
            home / "Research",
        ]
        read_scope = [str(path) for path in meaningful_roots if path.exists()]

        return {
            "default_mode": "Approval Mode",
            "modes": [
                {
                    "name": "Observation Mode",
                    "description": "Read-only. Cortex observes, indexes, summarizes, and updates memory without modifying anything.",
                },
                {
                    "name": "Approval Mode",
                    "description": "Default. Cortex can read automatically and must request approval before any modification.",
                },
                {
                    "name": "Automated Mode",
                    "description": "Allowed for selected safe categories like indexing and memory updates, but destructive actions still require approval.",
                },
            ],
            "read_permissions": [
                "Read files",
                "Search files",
                "Analyze files",
                "Index files",
                "Extract document contents",
                "Build embeddings",
                "Create summaries",
                "Build memory",
                "Build knowledge graphs",
                "Perform semantic retrieval",
            ],
            "modify_permissions": [
                "Edit files",
                "Create files",
                "Rename files",
                "Move files",
                "Delete files",
                "Install packages",
                "Change configurations",
                "Modify repositories",
                "Change system state",
            ],
            "ignored_paths": [
                "/proc",
                "/sys",
                "/dev",
                "/run",
                "/tmp",
            ],
            "read_scope": read_scope,
            "discovery_policy": "Read broadly across meaningful user data while pruning OS noise and requiring approval for any mutation.",
            "autonomous_discovery": [
                "Detect new repositories",
                "Detect new projects",
                "Detect new PDFs and documents",
                "Detect architecture changes",
                "Detect dependency changes",
                "Detect large downloads",
                "Proactively ask when a useful change is noticed",
            ],
            "approval_rules": [
                "Always explain the planned action before modification",
                "Always show affected files or resources",
                "Always explain the expected outcome",
                "Never use sudo automatically",
                "Never delete or modify without approval",
            ],
            "proactive_examples": [
                "I detected a new repository. Would you like an architecture summary?",
                "I found 12 new research papers. Would you like a consolidated summary?",
                "I detected major changes in the Cortex codebase. Would you like an updated architecture analysis?",
            ],
        }

    def _detect_todo_count(self, files: list[Path]) -> int:
        todo_pattern = re.compile(r"\b(TODO|FIXME|XXX)\b", re.IGNORECASE)
        count = 0
        for path in files:
            text = self._read_text(path, limit=60000)
            if not text:
                continue
            count += len(todo_pattern.findall(text))
        return count

    def _build_activity_feed(
        self,
        files: list[Path],
        repositories: list[str],
        concepts: list[str],
        warnings: list[str],
    ) -> list[ActivityFeedItem]:
        todo_count = self._detect_todo_count(files)
        architecture_changed = bool(repositories) and bool(concepts)
        follow_up_count = max(todo_count, 4 if architecture_changed else todo_count)

        feed = [
            ActivityFeedItem(
                title=f"Cortex indexed {len(repositories)} new repositories",
                detail=" ".join(repositories) if repositories else "No distinct project roots were discovered during this scan.",
                tone="success",
                count=len(repositories),
            ),
            ActivityFeedItem(
                title=f"Cortex learned {len(concepts)} new concepts",
                detail=" ".join(concepts) if concepts else "The current scan did not reveal enough structure to build a concept map.",
                tone="info",
                count=len(concepts),
            ),
            ActivityFeedItem(
                title=f"Cortex found {follow_up_count} TODOs",
                detail="Heuristic follow-up signals surfaced from the workspace scan and product brief.",
                tone="warning" if follow_up_count else "info",
                count=follow_up_count,
            ),
            ActivityFeedItem(
                title="Cortex detected architecture changes",
                detail=self._architecture_change_detail(warnings, repositories, concepts),
                tone="insight",
            ),
        ]

        return feed

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

    def _architecture_change_detail(self, warnings: list[str], repositories: list[str], concepts: list[str]) -> str:
        parts = [
            f"{len(repositories)} repository roots",
            f"{len(concepts)} active concepts",
        ]
        if warnings:
            parts.append(f"{len(warnings)} warnings worth tracking")
        return "Detected " + ", ".join(parts) + "."

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
