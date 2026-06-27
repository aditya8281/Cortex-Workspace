# tests/agents/integrity/test_context.py
from pathlib import Path

from backend.app.agents.integrity.model.context import (
    AnalysisContext,
    AnalysisScope,
    Classification,
    ExecutionProfile,
    IntegrityDomain,
    Priority,
    Severity,
)


def test_execution_profile_values():
    assert ExecutionProfile.FULL.value == "full"
    assert ExecutionProfile.INCREMENTAL.value == "incremental"


def test_analysis_scope_values():
    assert AnalysisScope.FULL_REPOSITORY.value == "full_repository"


def test_analysis_context_defaults():
    ctx = AnalysisContext(
        profile=ExecutionProfile.FULL,
        scope=AnalysisScope.FULL_REPOSITORY,
        repository_root=Path("/tmp"),
    )
    assert ctx.profile == ExecutionProfile.FULL
    assert ctx.changed_files is None
    assert ctx.target_engines is None


def test_integrity_domain_values():
    assert IntegrityDomain.STRUCTURAL.value == "structural"
    assert IntegrityDomain.SEMANTIC.value == "semantic"
    assert IntegrityDomain.EVOLUTION.value == "evolution"


def test_severity_ordering():
    assert Severity.CRITICAL > Severity.INSIGHT
    assert list(Severity) == [
        Severity.CRITICAL,
        Severity.HIGH,
        Severity.MEDIUM,
        Severity.LOW,
        Severity.INSIGHT,
    ]


def test_classification_values():
    assert Classification.MISSING.value == "missing"
    assert Classification.DRIFTED.value == "drifted"


def test_priority_values():
    assert Priority.P0.value == "P0"
    assert Priority.P3.value == "P3"
