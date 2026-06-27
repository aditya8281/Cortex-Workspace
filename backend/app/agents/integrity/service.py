"""IntegrityService — public API for repository integrity analysis."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from backend.app.agents.integrity.model import RepositoryKnowledgeModel
from backend.app.agents.integrity.model.context import ExecutionProfile
from backend.app.agents.integrity.model.finding import Finding
from backend.app.agents.integrity.model.metrics import ExecutionMetrics
from backend.app.agents.integrity.query import RepositoryQueryService
from backend.app.agents.integrity.views import DerivedViews
from backend.app.agents.integrity.workflow import IntegrityWorkflow


@dataclass
class IntegrityReport:
    model: RepositoryKnowledgeModel
    findings: list[Finding]
    metrics: ExecutionMetrics
    execution_profile: ExecutionProfile
    execution_time_ms: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class IntegrityService:
    """Public API for repository integrity analysis.

    Commands and skills call this service — they never access engines,
    views, or the workflow directly.
    """

    def __init__(self, repository_root: Path) -> None:
        self._workflow = IntegrityWorkflow(repository_root)
        self._root = repository_root

    def analyze(
        self,
        profile: ExecutionProfile = ExecutionProfile.FULL,
        changed_files: list[Path] | None = None,
    ) -> IntegrityReport:
        start = time.monotonic()

        model = self._workflow.build_model()
        findings, metrics = self._workflow.run(profile, changed_files)
        elapsed = int((time.monotonic() - start) * 1000)

        return IntegrityReport(
            model=model,
            findings=findings,
            metrics=metrics,
            execution_profile=profile,
            execution_time_ms=elapsed,
        )

    def analyze_incremental(self, changed_files: list[Path]) -> IntegrityReport:
        return self.analyze(
            profile=ExecutionProfile.INCREMENTAL,
            changed_files=changed_files,
        )

    def analyze_target(
        self,
        paths: list[Path],
        engines: list[str] | None = None,
    ) -> IntegrityReport:
        return self.analyze(
            profile=ExecutionProfile.TARGET,
            changed_files=paths,
        )

    def build_model(self) -> RepositoryKnowledgeModel:
        return self._workflow.build_model()

    def build_views(self, model: RepositoryKnowledgeModel) -> DerivedViews:
        return self._workflow.build_views(model)

    def query(self, model: RepositoryKnowledgeModel) -> RepositoryQueryService:
        return RepositoryQueryService(model)
