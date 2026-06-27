"""IntegrityWorkflow — orchestrates model building, engine execution, aggregation."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.app.agents.integrity.closure import DependencyClosureService
from backend.app.agents.integrity.extractors.python_extractor import (
    PythonExtractor,
)
from backend.app.agents.integrity.extractors.python_normalizer import (
    PythonNormalizer,
)
from backend.app.agents.integrity.model import RepositoryKnowledgeModel
from backend.app.agents.integrity.model.code_model import CodeModel
from backend.app.agents.integrity.model.context import (
    AnalysisContext,
    AnalysisScope,
    ExecutionProfile,
)
from backend.app.agents.integrity.model.documentation_model import (
    DocumentationModel,
)
from backend.app.agents.integrity.model.ecosystem_model import EcosystemModel
from backend.app.agents.integrity.model.finding import Finding
from backend.app.agents.integrity.model.metadata_model import (
    MetadataModel,
    RepositoryCapabilities,
)
from backend.app.agents.integrity.model.metrics import ExecutionMetrics
from backend.app.agents.integrity.model.relationship_model import (
    RelationshipModel,
)
from backend.app.agents.integrity.query import RepositoryQueryService
from backend.app.agents.integrity.registry import EngineRegistry
from backend.app.agents.integrity.report import Aggregator
from backend.app.agents.integrity.validation import Validator
from backend.app.agents.integrity.views import ViewRegistry


class IntegrityWorkflow:
    """Internal workflow orchestrator.

    Coordinates the pipeline stages:
    Discovery -> Collection -> Normalization -> Validation ->
    Model -> Views -> Analysis -> Aggregation -> Reporting
    """

    def __init__(self, repository_root: Path) -> None:
        self._root = repository_root
        self._view_registry = ViewRegistry()
        self._validator = Validator()
        self._engine_registry = EngineRegistry.get_instance()
        self._aggregator = Aggregator()
        self._closure = DependencyClosureService()

    def build_model(self) -> RepositoryKnowledgeModel:
        extractor = PythonExtractor()
        normalizer = PythonNormalizer()

        files: dict[Any, Any] = {}
        symbols: dict[Any, Any] = {}
        schemas: dict[Any, Any] = {}
        imports: list[Any] = []

        for path in sorted(self._root.rglob("*.py")):
            if any(
                part.startswith(".") or part in (".venv", "__pycache__", "node_modules", ".git") for part in path.parts
            ):
                continue
            try:
                raw = extractor.extract(path)
                entities = normalizer.normalize(raw)
                for ent in entities:
                    if hasattr(ent, "id"):
                        files[ent.id] = ent
                        for imp_str in getattr(ent, "raw_metadata", {}).get("imports", []):
                            imports.append({"file": str(path), "import": imp_str})
            except (SyntaxError, UnicodeDecodeError, OSError):
                continue

        now = datetime.now(timezone.utc)
        repo_hash = hashlib.md5(str(self._root).encode()).hexdigest()[:12]

        return RepositoryKnowledgeModel(
            metadata=MetadataModel(
                version="1.0",
                relationship_schema_version="1.0",
                repository_hash=repo_hash,
                generated_at=now,
                collector_versions={"python": "1.0"},
                capabilities=RepositoryCapabilities(
                    languages={"python"},
                    has_backend=True,
                ),
            ),
            code=CodeModel(
                files=files,
                directories=(set(self._root.iterdir()) if self._root.exists() else set()),
                symbols=symbols,
                imports=imports,
                schemas=schemas,
                types={},
                routes={},
                routers={},
                middleware={},
                models={},
                migrations={},
                db_config=None,
                components={},
                api_clients={},
                configs={},
            ),
            ecosystem=EcosystemModel(commands={}, skills={}, hooks={}, workflows={}, plans={}),
            documentation=DocumentationModel(plans={}, source_of_truths={}, adrs=[]),
            relationships=RelationshipModel(edges=[], relationship_schema_version="1.0"),
        )

    def build_views(self, model: RepositoryKnowledgeModel) -> Any:
        return self._view_registry.build(model)

    def build_context(
        self,
        profile: ExecutionProfile,
        changed: list[Path] | None = None,
    ) -> AnalysisContext:
        return AnalysisContext(
            profile=profile,
            scope=(AnalysisScope.DEPENDENCY_CLOSURE if changed else AnalysisScope.FULL_REPOSITORY),
            repository_root=self._root,
            changed_files=changed,
        )

    def run(
        self,
        profile: ExecutionProfile = ExecutionProfile.FULL,
        changed_files: list[Path] | None = None,
    ) -> tuple[list[Finding], ExecutionMetrics]:
        model = self.build_model()
        views = self.build_views(model)
        query = RepositoryQueryService(model)
        context = self.build_context(profile, changed_files)

        findings: list[Finding] = []
        engine_defs = self._engine_registry.for_profile(profile)

        for engine_def in engine_defs:
            try:
                engine = engine_def["cls"]()
                engine_findings = engine.analyze(model, query, views, context)
                findings.extend(engine_findings)
            except Exception:
                continue

        aggregate = self._aggregator.aggregate(findings)
        metrics = ExecutionMetrics(
            total_findings=aggregate.total_findings,
            by_severity=aggregate.by_severity,
            by_classification=aggregate.by_classification,
        )

        return findings, metrics
