"""Tests for Aggregator and Reporter."""

from backend.app.agents.integrity.report import Aggregator, Reporter
from backend.app.agents.integrity.model.finding import Finding
from backend.app.agents.integrity.model.context import (
    Severity,
    Classification,
    Priority,
)


def test_aggregator_empty():
    agg = Aggregator()
    result = agg.aggregate([])
    assert result.total_findings == 0


def test_aggregator_counts():
    findings = [
        Finding(
            title="f1",
            severity=Severity.HIGH,
            priority=Priority.P1,
            urgency=5,
            classification=Classification.DRIFTED,
            location="a.py",
        ),
        Finding(
            title="f2",
            severity=Severity.LOW,
            priority=Priority.P3,
            urgency=2,
            classification=Classification.UNUSED,
            location="b.py",
        ),
    ]
    agg = Aggregator()
    result = agg.aggregate(findings)
    assert result.total_findings == 2
    assert result.by_severity.get("HIGH") == 1
    assert result.by_severity.get("LOW") == 1


def test_reporter_markdown():
    findings = [
        Finding(
            title="test",
            severity=Severity.HIGH,
            priority=Priority.P1,
            urgency=5,
            classification=Classification.DRIFTED,
            location="a.py",
        ),
    ]
    agg = Aggregator()
    metrics = agg.aggregate(findings)
    reporter = Reporter()
    md = reporter.to_markdown(findings, metrics)
    assert "test" in md
    assert "HIGH" in md


def test_reporter_json():
    findings = [
        Finding(
            title="json test",
            severity=Severity.LOW,
            priority=Priority.P3,
            urgency=2,
            classification=Classification.UNUSED,
            location="a.py",
        ),
    ]
    agg = Aggregator()
    metrics = agg.aggregate(findings)
    reporter = Reporter()
    js = reporter.to_json(findings, metrics)
    assert "json test" in js
    assert "LOW" in js
