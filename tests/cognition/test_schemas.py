"""Tests for cognition and execution Pydantic schemas."""

import pytest
from pydantic import ValidationError

from backend.app.schemas.cognition.confidence import ConfidenceEstimate
from backend.app.schemas.cognition.error_analysis import (
    ErrorAnalysisCreate,
)
from backend.app.schemas.cognition.hypothesis import HypothesisCreate
from backend.app.schemas.cognition.task_plan import TaskPlanCreate, TaskPlanResponse
from backend.app.schemas.execution.tool_execution import (
    ToolExecutionCreate,
)
from backend.app.schemas.execution.workflow import WorkflowCreate, WorkflowResponse


class TestTaskPlanSchemas:
    def test_create_valid(self):
        schema = TaskPlanCreate(goal="Test goal")
        assert schema.goal == "Test goal"
        assert schema.steps is None

    def test_create_requires_goal(self):
        with pytest.raises(ValidationError):
            TaskPlanCreate()

    def test_response_from_attributes(self):
        data = {
            "id": 1,
            "user_id": 1,
            "goal": "Test",
            "steps": [],
            "current_step": 0,
            "status": "pending",
            "created_at": "2026-01-01T00:00:00",
        }
        schema = TaskPlanResponse(**data)
        assert schema.id == 1


class TestErrorAnalysisSchemas:
    def test_create_valid(self):
        schema = ErrorAnalysisCreate(error_type="ValueError", context={"key": "val"})
        assert schema.error_type == "ValueError"

    def test_create_requires_error_type(self):
        with pytest.raises(ValidationError):
            ErrorAnalysisCreate(context={})

    def test_create_defaults(self):
        schema = ErrorAnalysisCreate(error_type="TypeError")
        assert schema.severity == "info"
        assert schema.context == {}


class TestHypothesisSchemas:
    def test_create_defaults(self):
        schema = HypothesisCreate(hypothesis="Test H")
        assert schema.evidence_for is None
        assert schema.evidence_against is None

    def test_create_valid(self):
        schema = HypothesisCreate(
            hypothesis="X causes Y",
            evidence_for=[{"text": "proof"}],
            source="error_analysis",
        )
        assert schema.source == "error_analysis"


class TestConfidenceSchemas:
    def test_estimate_valid(self):
        schema = ConfidenceEstimate(task_type="planning", context={"goal": "test"})
        assert schema.task_type == "planning"

    def test_estimate_requires_task_type(self):
        with pytest.raises(ValidationError):
            ConfidenceEstimate()


class TestWorkflowSchemas:
    def test_create_requires_steps(self):
        with pytest.raises(ValidationError):
            WorkflowCreate(name="Test")

    def test_create_requires_name(self):
        with pytest.raises(ValidationError):
            WorkflowCreate(steps=[{"tool": "echo"}])

    def test_create_valid(self):
        schema = WorkflowCreate(name="Test WF", steps=[{"tool": "echo", "params": {"msg": "hi"}}])
        assert len(schema.steps) == 1

    def test_response_from_attributes(self):
        data = {
            "id": 1,
            "user_id": 1,
            "name": "WF",
            "steps": [],
            "status": "idle",
            "current_step": 0,
            "run_count": 0,
            "created_at": "2026-01-01T00:00:00",
        }
        schema = WorkflowResponse(**data)
        assert schema.name == "WF"


class TestToolExecutionSchemas:
    def test_create_valid(self):
        schema = ToolExecutionCreate(tool_name="search")
        assert schema.tool_name == "search"
        assert schema.parameters is None

    def test_create_requires_tool_name(self):
        with pytest.raises(ValidationError):
            ToolExecutionCreate()
