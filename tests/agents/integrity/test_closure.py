"""Tests for DependencyClosureService."""

import uuid
from pathlib import Path

from backend.app.agents.integrity.closure import (
    DependencyEdge,
    DependencyClosureService,
)


def test_dependency_edge():
    e = DependencyEdge(
        source_id=uuid.uuid4(), target_id=uuid.uuid4(), reason="imports"
    )
    assert e.reason == "imports"
    assert len(e.path) == 0


def test_empty_closure():
    svc = DependencyClosureService()
    result = svc.compute_impact_set([], None)
    assert len(result.directly_changed) == 0
    assert len(result.transitively_affected) == 0


def test_single_file_closure():
    svc = DependencyClosureService()
    result = svc.compute_impact_set(
        [Path("tests/test_demo.py")], None
    )
    assert len(result.directly_changed) == 1
    assert len(result.transitively_affected) == 0
