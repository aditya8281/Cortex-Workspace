"""Tests for IntegrityService and IntegrityWorkflow."""

from pathlib import Path

from backend.app.agents.integrity.service import IntegrityService, IntegrityReport
from backend.app.agents.integrity.model.context import ExecutionProfile


def test_service_init():
    svc = IntegrityService(repository_root=Path("."))
    assert svc is not None


def test_service_build_model():
    svc = IntegrityService(repository_root=Path("backend/app/agents/integrity"))
    model = svc.build_model()
    assert model is not None
    assert model.metadata is not None
    assert model.metadata.version == "1.0"


def test_service_analyze_full():
    svc = IntegrityService(repository_root=Path("backend/app/agents/integrity"))
    report = svc.analyze()
    assert isinstance(report, IntegrityReport)
    assert report.execution_profile == ExecutionProfile.FULL
    assert report.findings is not None
    assert report.execution_time_ms >= 0


def test_service_analyze_incremental():
    svc = IntegrityService(repository_root=Path("backend/app/agents/integrity"))
    report = svc.analyze_incremental(
        [Path("backend/app/agents/integrity/model/_base.py")]
    )
    assert report is not None
    assert report.execution_profile == ExecutionProfile.INCREMENTAL


def test_service_query():
    svc = IntegrityService(repository_root=Path("backend/app/agents/integrity"))
    model = svc.build_model()
    query = svc.query(model)
    assert query is not None
    assert hasattr(query, "find_by_id")


def test_service_build_views():
    svc = IntegrityService(repository_root=Path("backend/app/agents/integrity"))
    model = svc.build_model()
    views = svc.build_views(model)
    assert views is not None
    assert hasattr(views, "import_graph")
