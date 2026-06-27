"""Tests for Finding model."""

from backend.app.agents.integrity.model.context import (
    Classification,
    Priority,
    Severity,
)
from backend.app.agents.integrity.model.finding import (
    CandidateFix,
    Finding,
    FixType,
)


def test_finding_minimal():
    f = Finding(
        title="test finding",
        description="a test",
        severity=Severity.HIGH,
        priority=Priority.P1,
        urgency=5,
        classification=Classification.DRIFTED,
        location="app.py:42",
    )
    assert f.title == "test finding"
    assert f.fix is None
    assert isinstance(f.related_findings, list)
    assert f.confidence == 1.0


def test_finding_with_fix():
    fix = CandidateFix(fix_type=FixType.SCRIPT, fix_code="rm old_file.py")
    f = Finding(
        title="orphan file",
        description="unused file",
        severity=Severity.LOW,
        priority=Priority.P3,
        urgency=2,
        classification=Classification.UNUSED,
        location="old.py",
        fix=fix,
    )
    assert f.fix.fix_type == FixType.SCRIPT
    assert f.fix.autofix_available is True


def test_finding_full():
    f = Finding(
        title="migration conflict",
        description="two migrations target same table",
        severity=Severity.CRITICAL,
        priority=Priority.P0,
        urgency=10,
        classification=Classification.DUPLICATE,
        location="migrations/001.py",
        affected_components=["UserModel"],
        dependency_chain=["migrations/001 -> migrations/002"],
        root_cause="merge conflict",
        downstream_impact="schema inconsistency",
        recommendation="resolve migration order",
        confidence=0.95,
        related_findings=["F-002"],
        owner="backend-team",
        tags={"migration", "schema"},
        references=["docs/DATABASE.md"],
    )
    assert f.severity == Severity.CRITICAL
    assert f.priority == Priority.P0


def test_finding_defaults():
    f = Finding(
        title="defaults test",
        severity=Severity.INSIGHT,
        priority=Priority.P3,
        urgency=1,
        classification=Classification.INCONSISTENT,
        location="",
    )
    assert f.confidence == 1.0
