# System Understanding, Learning Loop & Desktop V1 Launch Plan (Weeks 11-12)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build system understanding (codebase analysis, dependency mapping), a learning loop (feedback collection, model improvement), and ship Desktop V1 via Tauri v2 — delivering a polished, autonomous AI workspace by end of Week 12.

**Architecture:** System understanding maps codebases into knowledge graphs automatically. Learning loop collects user feedback and agent performance metrics to improve future reasoning. Desktop V1 bundles backend + frontend into a native app with system tray, auto-update, and offline-first operation.

**Tech Stack:** Tauri v2 (Rust), React 19, FastAPI, PostgreSQL, Qdrant, Alembic, GitHub Actions.

## Global Constraints

- Python 3.12+, Node.js 20+, Rust 2024 edition
- TypeScript strict mode, ESLint zero warnings
- Python: ruff line-length 120, mypy strict
- Tauri v2: binary size < 50MB, cold start < 2s
- Desktop: Windows 10+, macOS 12+, Ubuntu 20.04+
- Auto-update: signed binaries, staged rollout
- Offline-first: all features work without internet
- Privacy: zero telemetry, no external API calls by default

---

## Task 1: System Understanding Engine

**Files:**
- Create: `backend/app/services/understanding/system_analyzer.py`
- Create: `backend/app/services/understanding/dependency_mapper.py`
- Create: `backend/tests/test_system_understanding.py`

**Interfaces:**
- Consumes: Task 1 from 02-WEEK-5-6-INDEXING.md (CodeIntelligence), Task 1 from 03-WEEK-7-8-AGENTS.md (UnifiedSearch)
- Produces: `SystemAnalyzer.analyze(path) -> SystemReport`, `DependencyMapper.map(project) -> DependencyGraph`

- [ ] **Step 1: Create app/services/understanding/system_analyzer.py**

```python
"""System analyzer: understand codebase structure, patterns, and architecture."""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ComponentInfo:
    name: str
    path: str
    type: str  # "service", "api", "model", "util", "config"
    language: str
    lines_of_code: int
    imports: list[str]
    exports: list[str]
    dependencies: list[str]


@dataclass
class PatternInfo:
    name: str
    description: str
    occurrences: int
    files: list[str]
    confidence: float


@dataclass
class ArchitectureInfo:
    layers: list[str]
    patterns: list[PatternInfo]
    entry_points: list[str]
    config_files: list[str]
    test_coverage: float


@dataclass
class SystemReport:
    root_path: str
    components: list[ComponentInfo]
    architecture: ArchitectureInfo
    total_files: int
    total_lines: int
    languages: dict[str, int]
    summary: str


class SystemAnalyzer:
    """Analyze a codebase to understand its structure and architecture.
    
    Identifies:
    - Components (services, APIs, models, utilities)
    - Design patterns (MVC, repository, factory, etc.)
    - Architecture layers (presentation, business, data)
    - Entry points and configuration
    """

    def __init__(self, code_intelligence=None):
        self._ci = code_intelligence

    async def analyze(self, root_path: str) -> SystemReport:
        """Analyze a codebase at the given path."""
        root = Path(root_path)
        
        components = []
        languages: dict[str, int] = {}
        total_lines = 0
        
        # Scan all source files
        for ext in ["*.py", "*.ts", "*.tsx", "*.js", "*.jsx", "*.rs", "*.go"]:
            for file_path in root.rglob(ext):
                if self._should_skip(file_path):
                    continue
                
                try:
                    content = file_path.read_text()
                    lines = len(content.splitlines())
                    total_lines += lines
                    
                    lang = file_path.suffix[1:]
                    languages[lang] = languages.get(lang, 0) + 1
                    
                    component = await self._analyze_file(file_path, root)
                    if component:
                        components.append(component)
                except Exception as e:
                    logger.debug("Failed to analyze %s: %s", file_path, e)
        
        # Detect patterns
        patterns = self._detect_patterns(components)
        
        # Identify architecture
        architecture = self._identify_architecture(components, patterns, root)
        
        return SystemReport(
            root_path=str(root),
            components=components,
            architecture=architecture,
            total_files=len(components),
            total_lines=total_lines,
            languages=languages,
            summary=self._generate_summary(components, architecture),
        )

    async def _analyze_file(self, file_path: Path, root: Path) -> ComponentInfo | None:
        """Analyze a single file."""
        rel_path = file_path.relative_to(root)
        content = file_path.read_text()
        
        # Detect imports
        imports = []
        for line in content.splitlines():
            if line.startswith("import ") or line.startswith("from "):
                imports.append(line.strip())
            elif line.startswith("from ") and "import" in line:
                imports.append(line.strip())
        
        # Detect exports (classes, functions)
        exports = []
        for line in content.splitlines():
            if line.startswith("class ") or line.startswith("def ") or line.startswith("export "):
                name = line.split("(")[0].split(":")[0].strip()
                exports.append(name)
        
        # Determine component type
        comp_type = self._classify_component(rel_path, content)
        
        return ComponentInfo(
            name=rel_path.stem,
            path=str(rel_path),
            type=comp_type,
            language=file_path.suffix[1:],
            lines_of_code=len(content.splitlines()),
            imports=imports[:20],  # Limit
            exports=exports[:20],
            dependencies=[],
        )

    def _classify_component(self, rel_path: Path, content: str) -> str:
        """Classify a file's component type."""
        path_str = str(rel_path).lower()
        
        if "api" in path_str or "router" in path_str or "endpoint" in path_str:
            return "api"
        elif "service" in path_str or "manager" in path_str:
            return "service"
        elif "model" in path_str or "schema" in path_str:
            return "model"
        elif "test" in path_str:
            return "test"
        elif "config" in path_str or "settings" in path_str:
            return "config"
        elif "util" in path_str or "helper" in path_str:
            return "util"
        
        # Content-based classification
        if "class " in content and "def " in content:
            return "service"
        elif "router" in content.lower():
            return "api"
        
        return "module"

    def _detect_patterns(self, components: list[ComponentInfo]) -> list[PatternInfo]:
        """Detect design patterns in the codebase."""
        patterns = []
        
        # Detect Repository Pattern
        repo_files = [c for c in components if "repository" in c.name.lower() or "repo" in c.name.lower()]
        if repo_files:
            patterns.append(PatternInfo(
                name="Repository Pattern",
                description="Data access abstraction layer",
                occurrences=len(repo_files),
                files=[c.path for c in repo_files],
                confidence=0.9,
            ))
        
        # Detect Factory Pattern
        factory_files = [c for c in components if "factory" in c.name.lower() or "create" in c.path.lower()]
        if factory_files:
            patterns.append(PatternInfo(
                name="Factory Pattern",
                description="Object creation abstraction",
                occurrences=len(factory_files),
                files=[c.path for c in factory_files],
                confidence=0.8,
            ))
        
        # Detect Service Layer
        service_files = [c for c in components if c.type == "service"]
        if len(service_files) >= 3:
            patterns.append(PatternInfo(
                name="Service Layer",
                description="Business logic abstraction",
                occurrences=len(service_files),
                files=[c.path for c in service_files],
                confidence=0.9,
            ))
        
        return patterns

    def _identify_architecture(
        self,
        components: list[ComponentInfo],
        patterns: list[PatternInfo],
        root: Path,
    ) -> ArchitectureInfo:
        """Identify the architecture style."""
        layers = []
        
        api_comps = [c for c in components if c.type == "api"]
        service_comps = [c for c in components if c.type == "service"]
        model_comps = [c for c in components if c.type == "model"]
        
        if api_comps:
            layers.append("API Layer")
        if service_comps:
            layers.append("Service Layer")
        if model_comps:
            layers.append("Data Layer")
        
        # Find entry points
        entry_points = []
        for c in components:
            if c.name in ["main", "app", "index", "__main__"]:
                entry_points.append(c.path)
        
        # Find config files
        config_files = [c.path for c in components if c.type == "config"]
        
        # Estimate test coverage
        test_count = len([c for c in components if c.type == "test"])
        total_count = len(components)
        test_coverage = test_count / total_count if total_count > 0 else 0.0
        
        return ArchitectureInfo(
            layers=layers,
            patterns=patterns,
            entry_points=entry_points,
            config_files=config_files,
            test_coverage=test_coverage,
        )

    def _generate_summary(self, components: list[ComponentInfo], arch: ArchitectureInfo) -> str:
        """Generate a human-readable summary."""
        total = len(components)
        apis = len([c for c in components if c.type == "api"])
        services = len([c for c in components if c.type == "service"])
        
        lines = [
            f"Codebase with {total} components ({apis} APIs, {services} services).",
            f"Architecture layers: {', '.join(arch.layers) or 'None detected'}.",
            f"Patterns detected: {', '.join(p.name for p in arch.patterns) or 'None'}.",
            f"Test coverage estimate: {arch.test_coverage:.0%}.",
        ]
        
        return " ".join(lines)

    def _should_skip(self, path: Path) -> bool:
        """Check if path should be skipped."""
        skip_dirs = {"node_modules", "__pycache__", ".git", "dist", "build", ".venv", "venv"}
        return any(part in skip_dirs for part in path.parts)
```

- [ ] **Step 2: Create app/services/understanding/dependency_mapper.py**

```python
"""Dependency mapper: map project dependencies and relationships."""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DependencyNode:
    id: str
    name: str
    version: str
    type: str  # "internal", "external", "stdlib"
    path: str | None = None
    dependencies: list[str] = field(default_factory=list)


@dataclass
class DependencyEdge:
    source: str
    target: str
    type: str  # "imports", "calls", "inherits"
    weight: int = 1


@dataclass
class DependencyGraph:
    nodes: dict[str, DependencyNode]
    edges: list[DependencyEdge]
    root_module: str
    external_deps: list[str]
    internal_deps: list[str]


class DependencyMapper:
    """Map dependencies between modules and external packages."""

    def __init__(self):
        pass

    async def map_project(self, root_path: str) -> DependencyGraph:
        """Map all dependencies in a project."""
        root = Path(root_path)
        nodes: dict[str, DependencyNode] = {}
        edges: list[DependencyEdge] = []
        
        # Find dependency files
        dep_files = {
            "python": list(root.rglob("requirements*.txt")) + list(root.rglob("pyproject.toml")),
            "node": list(root.rglob("package.json")),
            "rust": list(root.rglob("Cargo.toml")),
        }
        
        external_deps = []
        
        # Parse Python dependencies
        for req_file in dep_files["python"]:
            deps = self._parse_requirements(req_file)
            external_deps.extend(deps)
        
        # Parse Node dependencies
        for pkg_file in dep_files["node"]:
            deps = self._parse_package_json(pkg_file)
            external_deps.extend(deps)
        
        # Map internal dependencies
        for py_file in root.rglob("*.py"):
            if self._should_skip(py_file):
                continue
            
            try:
                content = py_file.read_text()
                node_id = str(py_file.relative_to(root))
                
                nodes[node_id] = DependencyNode(
                    id=node_id,
                    name=py_file.stem,
                    version="",
                    type="internal",
                    path=str(py_file.relative_to(root)),
                )
                
                # Extract imports
                imports = self._extract_imports(content)
                for imp in imports:
                    # Try to resolve to internal module
                    target_id = self._resolve_import(imp, root, py_file)
                    if target_id and target_id in nodes:
                        edges.append(DependencyEdge(
                            source=node_id,
                            target=target_id,
                            type="imports",
                        ))
            except Exception as e:
                logger.debug("Failed to map %s: %s", py_file, e)
        
        return DependencyGraph(
            nodes=nodes,
            edges=edges,
            root_module=root.name,
            external_deps=external_deps,
            internal_deps=list(nodes.keys()),
        )

    def _parse_requirements(self, path: Path) -> list[str]:
        """Parse requirements.txt or pyproject.toml."""
        deps = []
        try:
            content = path.read_text()
            if path.name == "requirements.txt":
                for line in content.splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and not line.startswith("-"):
                        deps.append(line.split("==")[0].split(">=")[0].split("<=")[0])
            elif path.name == "pyproject.toml":
                # Simple extraction
                if "dependencies" in content:
                    import re
                    deps = re.findall(r'"([a-zA-Z0-9_-]+)', content)
        except Exception:
            pass
        return deps

    def _parse_package_json(self, path: Path) -> list[str]:
        """Parse package.json dependencies."""
        import json
        try:
            data = json.loads(path.read_text())
            deps = list(data.get("dependencies", {}).keys())
            deps.extend(data.get("devDependencies", {}).keys())
            return deps
        except Exception:
            return []

    def _extract_imports(self, content: str) -> list[str]:
        """Extract import statements from Python code."""
        imports = []
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("from ") and "import" in line:
                module = line.split("from ")[1].split(" import")[0].strip()
                imports.append(module)
            elif line.startswith("import "):
                module = line.split("import ")[1].split(" as")[0].split(",")[0].strip()
                imports.append(module)
        return imports

    def _resolve_import(self, module: str, root: Path, current_file: Path) -> str | None:
        """Try to resolve an import to an internal module."""
        # Try relative import
        parts = module.split(".")
        potential = current_file.parent / "/".join(parts)
        if potential.with_suffix(".py").exists():
            return str(potential.with_suffix(".py").relative_to(root))
        
        # Try absolute import
        potential = root / "/".join(parts)
        if potential.with_suffix(".py").exists():
            return str(potential.with_suffix(".py").relative_to(root))
        
        return None

    def _should_skip(self, path: Path) -> bool:
        skip_dirs = {"node_modules", "__pycache__", ".git", "dist", "build", ".venv"}
        return any(part in skip_dirs for part in path.parts)
```

- [ ] **Step 3: Write tests**

```python
# backend/tests/test_system_understanding.py
"""Tests for system understanding engine."""
from __future__ import annotations
import pytest
import tempfile
from pathlib import Path
from app.services.understanding.system_analyzer import SystemAnalyzer
from app.services.understanding.dependency_mapper import DependencyMapper


@pytest.fixture
def sample_project():
    """Create a temporary project structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        # Create sample files
        (root / "main.py").write_text("""
from fastapi import FastAPI
from services.auth import AuthService

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello"}
""")
        
        (root / "services").mkdir()
        (root / "services" / "__init__.py").write_text("")
        (root / "services" / "auth.py").write_text("""
class AuthService:
    def login(self, username: str, password: str) -> bool:
        return True
""")
        
        (root / "models").mkdir()
        (root / "models" / "user.py").write_text("""
from dataclasses import dataclass

@dataclass
class User:
    id: int
    username: str
""")
        
        yield root


@pytest.mark.asyncio
async def test_system_analyzer(sample_project):
    analyzer = SystemAnalyzer()
    report = await analyzer.analyze(str(sample_project))
    
    assert report.total_files >= 2
    assert report.total_lines > 0
    assert "py" in report.languages
    assert report.summary


@pytest.mark.asyncio
async def test_system_analyzer_detects_services(sample_project):
    analyzer = SystemAnalyzer()
    report = await analyzer.analyze(str(sample_project))
    
    service_comps = [c for c in report.components if c.type == "service"]
    assert len(service_comps) >= 1


@pytest.mark.asyncio
async def test_dependency_mapper(sample_project):
    mapper = DependencyMapper()
    graph = await mapper.map_project(str(sample_project))
    
    assert graph.root_module == sample_project.name
    assert len(graph.internal_deps) >= 1
```

- [ ] **Step 4: Run tests**

Run: `PYTHONPATH=. pytest backend/tests/test_system_understanding.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/understanding/ backend/tests/test_system_understanding.py
git commit -m "feat: add system understanding engine"
```

---

## Task 2: Learning Loop & Feedback System

**Files:**
- Create: `backend/app/services/learning/feedback.py`
- Create: `backend/app/services/learning/metrics.py`
- Create: `backend/tests/test_learning.py`

**Interfaces:**
- Consumes: Task 1 from 03-WEEK-7-8-AGENTS.md (AgentRuntime)
- Produces: `FeedbackCollector.collect(rating, feedback)`, `MetricsCollector.record_event(event)`

- [ ] **Step 1: Create app/services/learning/feedback.py**

```python
"""Feedback collection for agent improvement."""
from __future__ import annotations
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class FeedbackItem:
    id: str
    agent_name: str
    task_id: str | None
    rating: int  # 1-5
    comment: str
    tags: list[str]
    timestamp: float
    metadata: dict[str, Any] = field(default_factory=dict)


class FeedbackCollector:
    """Collect and store user feedback on agent performance.
    
    Feedback is used to:
    - Improve agent prompts
    - Adjust temperature parameters
    - Identify failure patterns
    - Track quality over time
    """

    def __init__(self):
        self._feedback: list[FeedbackItem] = []

    async def collect(
        self,
        agent_name: str,
        rating: int,
        comment: str = "",
        task_id: str | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> FeedbackItem:
        """Collect a feedback item."""
        item = FeedbackItem(
            id=str(uuid.uuid4()),
            agent_name=agent_name,
            task_id=task_id,
            rating=max(1, min(5, rating)),
            comment=comment,
            tags=tags or [],
            timestamp=time.time(),
            metadata=metadata or {},
        )
        
        self._feedback.append(item)
        
        logger.info(
            "Feedback collected: agent=%s rating=%d comment=%s",
            agent_name,
            item.rating,
            comment[:50] if comment else "",
        )
        
        return item

    def get_feedback(
        self,
        agent_name: str | None = None,
        min_rating: int | None = None,
        limit: int = 100,
    ) -> list[FeedbackItem]:
        """Retrieve feedback items."""
        items = self._feedback
        
        if agent_name:
            items = [f for f in items if f.agent_name == agent_name]
        
        if min_rating is not None:
            items = [f for f in items if f.rating >= min_rating]
        
        return sorted(items, key=lambda x: x.timestamp, reverse=True)[:limit]

    def get_agent_stats(self, agent_name: str) -> dict[str, Any]:
        """Get statistics for an agent's feedback."""
        items = [f for f in self._feedback if f.agent_name == agent_name]
        
        if not items:
            return {"count": 0, "avg_rating": 0, "rating_distribution": {}}
        
        ratings = [f.rating for f in items]
        distribution = {i: ratings.count(i) for i in range(1, 6)}
        
        return {
            "count": len(items),
            "avg_rating": sum(ratings) / len(ratings),
            "rating_distribution": distribution,
            "recent_comments": [f.comment for f in items[:5] if f.comment],
        }

    def get_improvement_suggestions(self) -> list[str]:
        """Analyze feedback and suggest improvements."""
        suggestions = []
        
        # Find low-rated feedback
        low_rated = [f for f in self._feedback if f.rating <= 2]
        if low_rated:
            agents = set(f.agent_name for f in low_rated)
            for agent in agents:
                agent_feedback = [f for f in low_rated if f.agent_name == agent]
                suggestions.append(
                    f"Agent '{agent}' has {len(agent_feedback)} low ratings. "
                    f"Review and improve its system prompt."
                )
        
        # Find common tags
        all_tags = []
        for f in self._feedback:
            all_tags.extend(f.tags)
        
        if all_tags:
            from collections import Counter
            tag_counts = Counter(all_tags).most_common(3)
            for tag, count in tag_counts:
                if count >= 3:
                    suggestions.append(f"Common feedback tag: '{tag}' ({count} times)")
        
        return suggestions
```

- [ ] **Step 2: Create app/services/learning/metrics.py**

```python
"""Metrics collection for agent performance tracking."""
from __future__ import annotations
import logging
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class MetricEvent:
    event_type: str  # "agent_run", "tool_call", "error", "search"
    agent_name: str | None
    duration_ms: float
    success: bool
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class MetricsCollector:
    """Collect and analyze agent performance metrics.
    
    Tracks:
    - Agent execution times
    - Tool call success rates
    - Error frequencies
    - Search quality metrics
    """

    def __init__(self):
        self._events: list[MetricEvent] = []

    def record_event(self, event: MetricEvent) -> None:
        """Record a metric event."""
        self._events.append(event)
        
        logger.debug(
            "Metric: type=%s agent=%s duration=%.1fms success=%s",
            event.event_type,
            event.agent_name,
            event.duration_ms,
            event.success,
        )

    def get_agent_metrics(self, agent_name: str) -> dict[str, Any]:
        """Get metrics for a specific agent."""
        events = [e for e in self._events if e.agent_name == agent_name]
        
        if not events:
            return {
                "total_runs": 0,
                "success_rate": 0.0,
                "avg_duration_ms": 0.0,
                "error_rate": 0.0,
            }
        
        successful = [e for e in events if e.success]
        failed = [e for e in events if not e.success]
        durations = [e.duration_ms for e in events]
        
        return {
            "total_runs": len(events),
            "success_rate": len(successful) / len(events),
            "avg_duration_ms": sum(durations) / len(durations),
            "p95_duration_ms": sorted(durations)[int(len(durations) * 0.95)] if durations else 0,
            "error_rate": len(failed) / len(events),
            "total_errors": len(failed),
        }

    def get_tool_metrics(self) -> dict[str, dict[str, Any]]:
        """Get metrics grouped by tool name."""
        tool_events: dict[str, list[MetricEvent]] = {}
        
        for event in self._events:
            if event.event_type == "tool_call":
                tool_name = event.metadata.get("tool_name", "unknown")
                if tool_name not in tool_events:
                    tool_events[tool_name] = []
                tool_events[tool_name].append(event)
        
        result = {}
        for tool_name, events in tool_events.items():
            successful = [e for e in events if e.success]
            durations = [e.duration_ms for e in events]
            
            result[tool_name] = {
                "total_calls": len(events),
                "success_rate": len(successful) / len(events) if events else 0,
                "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
            }
        
        return result

    def get_performance_summary(self) -> dict[str, Any]:
        """Get overall performance summary."""
        if not self._events:
            return {"total_events": 0}
        
        agent_events = [e for e in self._events if e.event_type == "agent_run"]
        tool_events = [e for e in self._events if e.event_type == "tool_call"]
        error_events = [e for e in self._events if e.event_type == "error"]
        
        return {
            "total_events": len(self._events),
            "agent_runs": len(agent_events),
            "tool_calls": len(tool_events),
            "errors": len(error_events),
            "overall_success_rate": (
                sum(1 for e in self._events if e.success) / len(self._events)
            ),
            "avg_duration_ms": (
                sum(e.duration_ms for e in self._events) / len(self._events)
            ),
        }
```

- [ ] **Step 3: Write tests**

```python
# backend/tests/test_learning.py
"""Tests for learning loop."""
from __future__ import annotations
import pytest
from app.services.learning.feedback import FeedbackCollector
from app.services.learning.metrics import MetricsCollector, MetricEvent


@pytest.mark.asyncio
async def test_feedback_collection():
    collector = FeedbackCollector()
    item = await collector.collect(
        agent_name="coder",
        rating=4,
        comment="Good code generation",
    )
    
    assert item.rating == 4
    assert item.agent_name == "coder"
    assert item.comment == "Good code generation"


@pytest.mark.asyncio
async def test_feedback_stats():
    collector = FeedbackCollector()
    await collector.collect(agent_name="coder", rating=5)
    await collector.collect(agent_name="coder", rating=3)
    await collector.collect(agent_name="researcher", rating=4)
    
    stats = collector.get_agent_stats("coder")
    assert stats["count"] == 2
    assert stats["avg_rating"] == 4.0


def test_metrics_recording():
    collector = MetricsCollector()
    collector.record_event(MetricEvent(
        event_type="agent_run",
        agent_name="coder",
        duration_ms=150.0,
        success=True,
    ))
    
    metrics = collector.get_agent_metrics("coder")
    assert metrics["total_runs"] == 1
    assert metrics["success_rate"] == 1.0


def test_tool_metrics():
    collector = MetricsCollector()
    collector.record_event(MetricEvent(
        event_type="tool_call",
        agent_name="coder",
        duration_ms=50.0,
        success=True,
        metadata={"tool_name": "read_file"},
    ))
    collector.record_event(MetricEvent(
        event_type="tool_call",
        agent_name="coder",
        duration_ms=100.0,
        success=False,
        metadata={"tool_name": "execute_command"},
    ))
    
    tool_metrics = collector.get_tool_metrics()
    assert "read_file" in tool_metrics
    assert tool_metrics["read_file"]["success_rate"] == 1.0


def test_improvement_suggestions():
    collector = FeedbackCollector()
    
    for _ in range(5):
        await collector.collect(
            agent_name="coder",
            rating=1,
            comment="Too slow",
            tags=["performance"],
        )
    
    suggestions = collector.get_improvement_suggestions()
    assert len(suggestions) >= 1
    assert "coder" in suggestions[0]
```

- [ ] **Step 4: Run tests**

Run: `PYTHONPATH=. pytest backend/tests/test_learning.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/learning/ backend/tests/test_learning.py
git commit -m "feat: add learning loop with feedback and metrics"
```

---

## Task 3: Learning API Endpoints

**Files:**
- Create: `backend/app/api/v1/learning.py`
- Create: `backend/tests/test_learning_api.py`

**Interfaces:**
- Consumes: Task 2 (FeedbackCollector, MetricsCollector)
- Produces: `POST /api/v1/learning/feedback`, `GET /api/v1/learning/metrics`

- [ ] **Step 1: Create app/api/v1/learning.py**

```python
"""Learning API endpoints."""
from __future__ import annotations
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any

router = APIRouter(prefix="/learning", tags=["learning"])

# Global instances (replace with DI in production)
_feedback_collector = None
_metrics_collector = None


def _get_feedback():
    global _feedback_collector
    if _feedback_collector is None:
        from app.services.learning.feedback import FeedbackCollector
        _feedback_collector = FeedbackCollector()
    return _feedback_collector


def _get_metrics():
    global _metrics_collector
    if _metrics_collector is None:
        from app.services.learning.metrics import MetricsCollector
        _metrics_collector = MetricsCollector()
    return _metrics_collector


class FeedbackRequest(BaseModel):
    agent_name: str
    rating: int
    comment: str = ""
    task_id: str | None = None
    tags: list[str] = []


class FeedbackResponse(BaseModel):
    id: str
    agent_name: str
    rating: int
    status: str


class MetricsResponse(BaseModel):
    overall: dict[str, Any]
    agents: dict[str, dict[str, Any]]
    tools: dict[str, dict[str, Any]]


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest):
    """Submit feedback on agent performance."""
    collector = _get_feedback()
    item = await collector.collect(
        agent_name=request.agent_name,
        rating=request.rating,
        comment=request.comment,
        task_id=request.task_id,
        tags=request.tags,
    )
    
    return FeedbackResponse(
        id=item.id,
        agent_name=item.agent_name,
        rating=item.rating,
        status="collected",
    )


@router.get("/feedback")
async def get_feedback(agent_name: str | None = None, limit: int = 50):
    """Get feedback items."""
    collector = _get_feedback()
    items = collector.get_feedback(agent_name=agent_name, limit=limit)
    
    return [
        {
            "id": f.id,
            "agent_name": f.agent_name,
            "rating": f.rating,
            "comment": f.comment,
            "tags": f.tags,
            "timestamp": f.timestamp,
        }
        for f in items
    ]


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get performance metrics."""
    metrics = _get_metrics()
    
    return MetricsResponse(
        overall=metrics.get_performance_summary(),
        agents={
            name: metrics.get_agent_metrics(name)
            for name in set(e.agent_name for e in metrics._events if e.agent_name)
        },
        tools=metrics.get_tool_metrics(),
    )


@router.get("/suggestions")
async def get_suggestions():
    """Get improvement suggestions based on feedback."""
    collector = _get_feedback()
    suggestions = collector.get_improvement_suggestions()
    
    return {"suggestions": suggestions}
```

- [ ] **Step 2: Register router**

Add to `backend/app/api/router.py`:

```python
from app.api.v1.learning import router as learning_router
api_router.include_router(learning_router, prefix="/v1")
```

- [ ] **Step 3: Write tests**

```python
# backend/tests/test_learning_api.py
"""Tests for learning API."""
from __future__ import annotations
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_submit_feedback():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/learning/feedback", json={
            "agent_name": "coder",
            "rating": 4,
            "comment": "Great code generation",
            "tags": ["quality"],
        })
    
    assert response.status_code == 200
    data = response.json()
    assert data["rating"] == 4
    assert data["status"] == "collected"


@pytest.mark.asyncio
async def test_get_feedback():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Submit first
        await client.post("/api/v1/learning/feedback", json={
            "agent_name": "coder",
            "rating": 5,
        })
        
        # Get
        response = await client.get("/api/v1/learning/feedback")
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_metrics():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/learning/metrics")
    
    assert response.status_code == 200
    data = response.json()
    assert "overall" in data
```

- [ ] **Step 4: Run tests**

Run: `PYTHONPATH=. pytest backend/tests/test_learning_api.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/v1/learning.py backend/app/api/router.py backend/tests/test_learning_api.py
git commit -m "feat: add learning API endpoints"
```

---

## Task 4: Desktop App — Tauri v2 Scaffold

**Files:**
- Create: `desktop/` directory structure
- Create: `desktop/src-tauri/Cargo.toml`
- Create: `desktop/src-tauri/src/main.rs`
- Create: `desktop/src-tauri/tauri.conf.json`
- Create: `desktop/package.json`

**Interfaces:**
- Consumes: Backend FastAPI app, Frontend Next.js app
- Produces: Native desktop app with system tray, auto-update

- [ ] **Step 1: Create desktop directory structure**

```bash
mkdir -p desktop/src-tauri/src
mkdir -p desktop/src-tauri/icons
```

- [ ] **Step 2: Create desktop/package.json**

```json
{
  "name": "cortex-desktop",
  "version": "1.0.0",
  "description": "Cortex - Local AI Workspace",
  "private": true,
  "scripts": {
    "dev": "tauri dev",
    "build": "tauri build",
    "tauri": "tauri"
  },
  "dependencies": {
    "@tauri-apps/api": "^2.0.0"
  },
  "devDependencies": {
    "@tauri-apps/cli": "^2.0.0"
  }
}
```

- [ ] **Step 3: Create desktop/src-tauri/Cargo.toml**

```toml
[package]
name = "cortex-desktop"
version = "1.0.0"
edition = "2024"

[build-dependencies]
tauri-build = { version = "2", features = [] }

[dependencies]
tauri = { version = "2", features = ["tray-icon", "macos-private-api"] }
tauri-plugin-shell = "2"
serde = { version = "1", features = ["derive"] }
serde_json = "1"
tokio = { version = "1", features = ["full"] }

[features]
default = ["custom-protocol"]
custom-protocol = ["tauri/custom-protocol"]
```

- [ ] **Step 4: Create desktop/src-tauri/build.rs**

```rust
fn main() {
    tauri_build::build()
}
```

- [ ] **Step 5: Create desktop/src-tauri/src/main.rs**

```rust
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::{Manager, SystemTray, SystemTrayEvent};

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! Welcome to Cortex.", name)
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![greet])
        .setup(|app| {
            // System tray
            let tray = SystemTray::new()
                .with_tooltip("Cortex - Local AI Workspace")
                .build(app)?;
            
            Ok(())
        })
        .on_system_tray_event(|app, event| {
            match event {
                SystemTrayEvent::DoubleClick {
                    position: _,
                    size: _,
                    ..
                } => {
                    // Show main window
                    if let Some(window) = app.get_window("main") {
                        window.show().unwrap();
                        window.set_focus().unwrap();
                    }
                }
                _ => {}
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

- [ ] **Step 6: Create desktop/src-tauri/tauri.conf.json**

```json
{
  "build": {
    "beforeDevCommand": "cd ../frontend && npm run dev",
    "beforeBuildCommand": "cd ../frontend && npm run build",
    "devPath": "http://localhost:3000",
    "frontendDist": "../frontend/out"
  },
  "package": {
    "productName": "Cortex"
  },
  "tauri": {
    "allowlist": {
      "all": false,
      "shell": {
        "all": false,
        "open": true
      }
    },
    "bundle": {
      "active": true,
      "icon": [
        "icons/icon.png"
      ],
      "identifier": "com.cortex.desktop",
      "targets": "all"
    },
    "security": {
      "csp": null
    },
    "windows": [
      {
        "title": "Cortex",
        "width": 1280,
        "height": 800,
        "minWidth": 800,
        "minHeight": 600,
        "resizable": true,
        "fullscreen": false,
        "visible": false
      }
    ],
    "systemTray": {
      "iconPath": "icons/icon.png",
      "iconAsTemplate": true
    }
  }
}
```

- [ ] **Step 7: Create desktop/build.rs**

```rust
fn main() {
    tauri_build::build()
}
```

- [ ] **Step 8: Verify Tauri config**

Run: `cd desktop && cargo check`
Expected: No errors

- [ ] **Step 9: Commit**

```bash
git add desktop/
git commit -m "feat: add Tauri v2 desktop scaffold"
```

---

## Task 5: Desktop — Backend Bundling

**Files:**
- Create: `desktop/src-tauri/src/backend.rs`
- Create: `desktop/src-tauri/src/sidecar.rs`

**Interfaces:**
- Consumes: Backend FastAPI app (bundled as Python binary)
- Produces: Embedded backend that starts with the desktop app

- [ ] **Step 1: Create desktop/src-tauri/src/backend.rs**

```rust
use std::process::{Child, Command};
use std::sync::Arc;
use tokio::sync::Mutex;

pub struct BackendManager {
    process: Option<Child>,
    port: u16,
}

impl BackendManager {
    pub fn new(port: u16) -> Self {
        Self {
            process: None,
            port,
        }
    }

    pub async fn start(&mut self) -> Result<(), String> {
        let python_path = Self::find_python().ok_or("Python not found")?;
        
        let mut cmd = Command::new(python_path);
        cmd.arg("-m")
            .arg("uvicorn")
            .arg("app.main:app")
            .arg("--host")
            .arg("127.0.0.1")
            .arg("--port")
            .arg(self.port.to_string());
        
        self.process = Some(cmd.spawn().map_err(|e| e.to_string())?);
        
        Ok(())
    }

    pub fn stop(&mut self) {
        if let Some(mut child) = self.process.take() {
            let _ = child.kill();
        }
    }

    fn find_python() -> Option<String> {
        // Try common Python locations
        let paths = ["python3", "python", "python3.12", "python3.11"];
        
        for path in paths {
            if Command::new(path)
                .arg("--version")
                .output()
                .is_ok()
            {
                return Some(path.to_string());
            }
        }
        
        None
    }
}

impl Drop for BackendManager {
    fn drop(&mut self) {
        self.stop();
    }
}
```

- [ ] **Step 2: Update main.rs to use backend**

```rust
// Add to main.rs
mod backend;
mod sidecar;

use backend::BackendManager;
use std::sync::Arc;
use tokio::sync::Mutex;

fn main() {
    let backend = Arc::new(Mutex::new(BackendManager::new(8000)));
    
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![greet])
        .setup(move |app| {
            // Start backend in background
            let backend = backend.clone();
            tokio::spawn(async move {
                let mut manager = backend.lock().await;
                if let Err(e) = manager.start().await {
                    eprintln!("Failed to start backend: {}", e);
                }
            });
            
            // Show window after setup
            if let Some(window) = app.get_window("main") {
                window.show().unwrap();
            }
            
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

- [ ] **Step 3: Verify build**

Run: `cd desktop && cargo check`
Expected: No errors

- [ ] **Step 4: Commit**

```bash
git add desktop/src-tauri/src/
git commit -m "feat: add backend bundling for desktop"
```

---

## Task 6: Desktop — Auto-Update

**Files:**
- Create: `desktop/src-tauri/src/updater.rs`
- Modify: `desktop/src-tauri/tauri.conf.json`

**Interfaces:**
- Consumes: GitHub Releases API
- Produces: Automatic update checking and installation

- [ ] **Step 1: Create desktop/src-tauri/src/updater.rs**

```rust
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct UpdateInfo {
    pub version: String,
    pub notes: String,
    pub pub_date: String,
    pub platforms: std::collections::HashMap<String, PlatformInfo>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PlatformInfo {
    pub signature: String,
    pub url: String,
}

pub struct Updater {
    repo: String,
    current_version: String,
}

impl Updater {
    pub fn new(repo: &str, current_version: &str) -> Self {
        Self {
            repo: repo.to_string(),
            current_version: current_version.to_string(),
        }
    }

    pub async fn check_for_updates(&self) -> Result<Option<UpdateInfo>, String> {
        let url = format!(
            "https://api.github.com/repos/{}/releases/latest",
            self.repo
        );
        
        let client = reqwest::Client::new();
        let response = client
            .get(&url)
            .header("User-Agent", "Cortex-Desktop")
            .send()
            .await
            .map_err(|e| e.to_string())?;
        
        if !response.status().is_success() {
            return Ok(None);
        }
        
        let release: serde_json::Value = response
            .json()
            .await
            .map_err(|e| e.to_string())?;
        
        let version = release["tag_name"]
            .as_str()
            .unwrap_or("")
            .trim_start_matches('v');
        
        if version != self.current_version {
            // Parse platforms
            let mut platforms = std::collections::HashMap::new();
            
            if let Some(assets) = release["assets"].as_array() {
                for asset in assets {
                    let name = asset["name"].as_str().unwrap_or("");
                    let url = asset["browser_download_url"].as_str().unwrap_or("");
                    
                    let platform = if name.contains("msi") || name.contains("exe") {
                        "windows-x86_64"
                    } else if name.contains("app.tar") {
                        "darwin-x86_64"
                    } else if name.contains("AppImage") || name.contains(".deb") {
                        "linux-x86_64"
                    } else {
                        continue;
                    };
                    
                    platforms.insert(
                        platform.to_string(),
                        PlatformInfo {
                            signature: "".to_string(),
                            url: url.to_string(),
                        },
                    );
                }
            }
            
            return Ok(Some(UpdateInfo {
                version: version.to_string(),
                notes: release["body"].as_str().unwrap_or("").to_string(),
                pub_date: release["published_at"].as_str().unwrap_or("").to_string(),
                platforms,
            }));
        }
        
        Ok(None)
    }
}
```

- [ ] **Step 2: Add updater to Cargo.toml**

```toml
[dependencies]
reqwest = { version = "0.11", features = ["json"] }
```

- [ ] **Step 3: Update tauri.conf.json for updater**

```json
{
  "tauri": {
    "updater": {
      "active": true,
      "dialog": true,
      "endpoints": [
        "https://github.com/cortex-ai/cortex-desktop/releases/latest/download/latest.json"
      ]
    }
  }
}
```

- [ ] **Step 4: Commit**

```bash
git add desktop/src-tauri/src/updater.rs desktop/src-tauri/Cargo.toml desktop/src-tauri/tauri.conf.json
git commit -m "feat: add auto-update for desktop"
```

---

## Task 7: Desktop — System Tray & Global Shortcut

**Files:**
- Create: `desktop/src-tauri/src/tray.rs`
- Create: `desktop/src-tauri/src/shortcut.rs`

**Interfaces:**
- Consumes: Tauri SystemTray API
- Produces: System tray with quick actions, global shortcut for quick search

- [ ] **Step 1: Create desktop/src-tauri/src/tray.rs**

```rust
use tauri::{
    AppHandle, CustomMenuItem, Manager, Menu, MenuItem, SystemTray,
    SystemTrayEvent, SystemTrayMenu,
};

pub fn create_system_tray() -> SystemTray {
    let show = CustomMenuItem::new("show".to_string(), "Show Cortex");
    let hide = CustomMenuItem::new("hide".to_string(), "Hide Cortex");
    let search = CustomMenuItem::new("search".to_string(), "Quick Search (Ctrl+Space)");
    let quit = CustomMenuItem::new("quit".to_string(), "Quit");
    
    let tray_menu = SystemTrayMenu::new()
        .add_item(show)
        .add_item(hide)
        .add_native_item(MenuItem::Separator)
        .add_item(search)
        .add_native_item(MenuItem::Separator)
        .add_item(quit);
    
    SystemTray::new().with_menu(tray_menu)
}

pub fn handle_tray_event(app: &AppHandle, event: SystemTrayEvent) {
    match event {
        SystemTrayEvent::MenuItemClick { id, .. } => {
            match id.as_str() {
                "show" => {
                    if let Some(window) = app.get_window("main") {
                        window.show().unwrap();
                        window.set_focus().unwrap();
                    }
                }
                "hide" => {
                    if let Some(window) = app.get_window("main") {
                        window.hide().unwrap();
                    }
                }
                "search" => {
                    // Open search window
                    if let Some(window) = app.get_window("main") {
                        window.show().unwrap();
                        window.set_focus().unwrap();
                        window.eval("window.dispatchEvent(new CustomEvent('open-search'))").unwrap();
                    }
                }
                "quit" => {
                    std::process::exit(0);
                }
                _ => {}
            }
        }
        SystemTrayEvent::DoubleClick { .. } => {
            if let Some(window) = app.get_window("main") {
                window.show().unwrap();
                window.set_focus().unwrap();
            }
        }
        _ => {}
    }
}
```

- [ ] **Step 2: Create desktop/src-tauri/src/shortcut.rs**

```rust
use tauri::{AppHandle, GlobalShortcutManager, Manager};

pub fn register_shortcuts(app: &AppHandle) -> Result<(), String> {
    let mut shortcut_manager = app.global_shortcut();
    
    // Ctrl+Space for quick search
    shortcut_manager
        .register("Ctrl+Space", move || {
            // Toggle search overlay
        })
        .map_err(|e| e.to_string())?;
    
    Ok(())
}

pub fn unregister_shortcuts(app: &AppHandle) -> Result<(), String> {
    let mut shortcut_manager = app.global_shortcut();
    shortcut_manager.unregister_all().map_err(|e| e.to_string())?;
    Ok(())
}
```

- [ ] **Step 3: Update main.rs to use tray and shortcuts**

```rust
mod tray;
mod shortcut;

// In setup:
let system_tray = tray::create_system_tray();
let app = tauri::Builder::default()
    .system_tray(system_tray)
    .on_system_tray_event(|app, event| {
        tray::handle_tray_event(app, event);
    })
    .setup(|app| {
        shortcut::register_shortcuts(app.handle())?;
        Ok(())
    })
    .build(tauri::generate_context!())
    .expect("error while building tauri application");
```

- [ ] **Step 4: Commit**

```bash
git add desktop/src-tauri/src/tray.rs desktop/src-tauri/src/shortcut.rs
git commit -m "feat: add system tray and global shortcuts"
```

---

## Task 8: CI/CD — GitHub Actions for Desktop

**Files:**
- Create: `.github/workflows/desktop-build.yml`

**Interfaces:**
- Consumes: Tauri build system
- Produces: Automated builds for Windows, macOS, Linux

- [ ] **Step 1: Create .github/workflows/desktop-build.yml**

```yaml
name: Desktop Build

on:
  push:
    tags:
      - "v*"
  workflow_dispatch:

jobs:
  build:
    strategy:
      fail-fast: false
      matrix:
        include:
          - platform: "windows-latest"
            target: "x86_64-pc-windows-msvc"
          - platform: "macos-latest"
            target: "x86_64-apple-darwin"
          - platform: "ubuntu-20.04"
            target: "x86_64-unknown-linux-gnu"

    runs-on: ${{ matrix.platform }}

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"

      - name: Setup Rust
        uses: dtolnay/rust-toolchain@stable
        with:
          targets: ${{ matrix.target }}

      - name: Install dependencies (Ubuntu)
        if: matrix.platform == 'ubuntu-20.04'
        run: |
          sudo apt-get update
          sudo apt-get install -y libgtk-3-dev libwebkit2gtk-4.0-dev libappindicator3-dev librsvg2-dev

      - name: Install frontend dependencies
        run: cd frontend && npm ci

      - name: Build frontend
        run: cd frontend && npm run build

      - name: Build desktop app
        uses: tauri-apps/tauri-action@v0
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          TAURI_SIGNING_PRIVATE_KEY: ${{ secrets.TAURI_SIGNING_PRIVATE_KEY }}
        with:
          tauriScript: cargo tauri
          args: --target ${{ matrix.target }}

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: desktop-${{ matrix.platform }}
          path: |
            desktop/src-tauri/target/release/bundle/**/*
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/desktop-build.yml
git commit -m "ci: add desktop build workflow"
```

---

## Task 9: Integration Testing & Final QA

**Files:**
- Create: `tests/test_integration.py`
- Create: `tests/test_desktop_integration.py`

**Interfaces:**
- Consumes: All previous tasks
- Produces: End-to-end test suite

- [ ] **Step 1: Create integration test**

```python
# tests/test_integration.py
"""End-to-end integration tests."""
from __future__ import annotations
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
    
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_full_workflow():
    """Test a complete user workflow."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register
        reg_response = await client.post("/api/auth/register", json={
            "username": "testuser",
            "password": "TestPass123!",
        })
        assert reg_response.status_code in (200, 409)
        
        # Login
        login_response = await client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "TestPass123!",
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            
            # Search
            search_response = await client.post("/api/v1/agents/run", json={
                "agent_name": "coder",
                "task": "list files",
            }, headers=headers)
            
            assert search_response.status_code == 200
```

- [ ] **Step 2: Run integration tests**

Run: `PYTHONPATH=. pytest tests/test_integration.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add integration tests"
```

### Migration Steps
No new SQLAlchemy models in this plan. Feedback and metrics use in-memory storage. For production, persist to PostgreSQL:
1. Create `backend/app/models/learning.py` (FeedbackItem, MetricEvent tables)
2. Run: `alembic revision --autogenerate -m "add_feedback_metric_tables"`
3. Run: `alembic upgrade head`
4. Verify: `PYTHONPATH=. pytest tests/test_learning.py tests/test_learning_api.py -v`

### API Versioning
All new endpoints must use `/api/v1/{resource}` prefix. Learning routes already conform:
- `POST /api/v1/learning/feedback` ✓
- `GET /api/v1/learning/feedback` ✓
- `GET /api/v1/learning/metrics` ✓
- `GET /api/v1/learning/suggestions` ✓

---

## Summary

By end of Week 12, Cortex has:

1. **System Understanding** — Codebase analysis, pattern detection, architecture mapping
2. **Dependency Mapper** — Project dependency graph visualization
3. **Learning Loop** — User feedback collection, performance metrics tracking
4. **Metrics Collector** — Agent execution times, tool success rates
5. **Desktop V1** — Native app via Tauri v2 (Windows, macOS, Linux)
6. **System Tray** — Quick actions, search shortcut
7. **Auto-Update** — Signed binaries, staged rollout
8. **CI/CD** — Automated builds for all platforms
9. **Integration Tests** — End-to-end workflow validation

### Cross-References
- **From 03-WEEK-7-8-AGENTS.md**: Agents integrated into desktop launcher
- **From 04-WEEK-9-10-INTELLIGENCE.md**: Intelligence features accessible from desktop
- **From 00-WEEK-1-2-FOUNDATION.md**: Auth and vault integrated into desktop flow

---

## Complete 90-Day Roadmap Summary

| Weeks | Focus | Key Deliverables |
|-------|-------|------------------|
| 1-2 | Foundation | Auth, vault, desktop scaffold, CI/CD |
| 3-4 | Memory | Vector DB, embeddings, repo scanner, memory UI |
| 5-6 | Indexing | Code intelligence, knowledge graph, graph viz |
| 7-8 | Agents | Unified search, agent runtime, Coder/Researcher agents |
| 9-10 | Intelligence | Reasoning, planning, multi-agent orchestration |
| 11-12 | Launch | System understanding, learning loop, Desktop V1 |
