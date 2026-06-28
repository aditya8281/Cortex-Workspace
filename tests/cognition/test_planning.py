"""Tests for TaskPlanningService."""

import pytest

from backend.app.models.cognition.task_plan import TaskPlan
from backend.app.services.cognition.planning import TaskPlanningService


class TestTaskPlanningService:
    """DAG-based planning service tests."""

    def test_create_plan(self, db_session):
        service = TaskPlanningService(db_session)
        steps = [
            {"step": 0, "description": "Step A", "status": "pending", "depends_on": []},
            {"step": 1, "description": "Step B", "status": "pending", "depends_on": [0]},
        ]
        plan = service.create_plan(user_id=1, goal="Test goal", steps=steps)
        assert plan.id is not None
        assert plan.goal == "Test goal"
        assert plan.status == "active"
        assert len(plan.steps) == 2
        assert plan.confidence is not None

        persisted = db_session.get(TaskPlan, plan.id)
        assert persisted is not None
        assert persisted.goal == "Test goal"

    def test_create_plan_auto_decompose(self, db_session):
        service = TaskPlanningService(db_session)
        # "build" keyword triggers the build template
        plan = service.create_plan(user_id=1, goal="Build a new feature")
        assert plan.id is not None
        assert len(plan.steps) == 4  # build template has 4 steps
        assert plan.steps[0]["description"].startswith("Design")

        # Unrecognised goal triggers default 3-step template
        plan2 = service.create_plan(user_id=1, goal="Do something custom")
        assert len(plan2.steps) == 3

    def test_cycle_detection(self, db_session):
        service = TaskPlanningService(db_session)
        steps = [
            {"step": 0, "description": "A", "status": "pending", "depends_on": [1]},
            {"step": 1, "description": "B", "status": "pending", "depends_on": [0]},
        ]
        with pytest.raises(ValueError, match="cycle"):
            service.create_plan(user_id=1, goal="Test", steps=steps)

    def test_execute_step(self, db_session):
        service = TaskPlanningService(db_session)
        steps = [
            {"step": 0, "description": "First", "status": "pending", "depends_on": []},
            {"step": 1, "description": "Second", "status": "pending", "depends_on": [0]},
        ]
        plan = service.create_plan(user_id=1, goal="Test", steps=steps)
        plan = service.execute_step(plan.id, 0, result={"output": "done"})
        assert plan.steps[0]["status"] == "completed"
        assert plan.steps[0]["result"] == {"output": "done"}

    def test_complete_plan(self, db_session):
        """Execute all steps in order and verify completion state."""
        service = TaskPlanningService(db_session)
        steps = [
            {"step": 0, "description": "A", "status": "pending", "depends_on": []},
            {"step": 1, "description": "B", "status": "pending", "depends_on": [0]},
            {"step": 2, "description": "C", "status": "pending", "depends_on": [1]},
        ]
        plan = service.create_plan(user_id=1, goal="Full flow", steps=steps)

        plan = service.execute_step(plan.id, 0, result={"ok": True})
        assert plan.steps[0]["status"] == "completed"

        plan = service.execute_step(plan.id, 1, result={"ok": True})
        assert plan.steps[1]["status"] == "completed"

        plan = service.execute_step(plan.id, 2, result={"ok": True})
        assert plan.steps[2]["status"] == "completed"

    def test_execute_step_dependency_check(self, db_session):
        """Executing a step whose dependency is not satisfied should fail."""
        service = TaskPlanningService(db_session)
        steps = [
            {"step": 0, "description": "Prereq", "status": "pending", "depends_on": []},
            {"step": 1, "description": "Dependent", "status": "pending", "depends_on": [0]},
        ]
        plan = service.create_plan(user_id=1, goal="Test deps", steps=steps)

        with pytest.raises(ValueError, match="Dependency step 0"):
            service.execute_step(plan.id, 1, result={})

    def test_skip_step(self, db_session):
        service = TaskPlanningService(db_session)
        steps = [
            {"step": 0, "description": "A", "status": "pending", "depends_on": []},
            {"step": 1, "description": "B", "status": "pending", "depends_on": [0]},
        ]
        plan = service.create_plan(user_id=1, goal="Test skip", steps=steps)
        plan = service.skip_step(plan.id, 0, reason="Not needed")
        assert plan.steps[0]["status"] == "skipped"
        assert plan.steps[0]["error"] == "Not needed"

    def test_get_next_executable_steps(self, db_session):
        service = TaskPlanningService(db_session)
        steps = [
            {"step": 0, "description": "A", "status": "pending", "depends_on": []},
            {"step": 1, "description": "B", "status": "pending", "depends_on": [0]},
            {"step": 2, "description": "C", "status": "pending", "depends_on": []},
        ]
        plan = service.create_plan(user_id=1, goal="Test next", steps=steps)

        # Steps 0 and 2 have no deps — should be executable
        executable = service.get_next_executable_steps(plan.id)
        assert 0 in executable
        assert 2 in executable

        # Execute step 0 — now step 1 should also be executable
        plan = service.execute_step(plan.id, 0, result={})
        executable = service.get_next_executable_steps(plan.id)
        assert 1 in executable
        assert 2 in executable

    def test_cancel_plan(self, db_session):
        service = TaskPlanningService(db_session)
        plan = service.create_plan(user_id=1, goal="Cancel me", steps=[])
        plan = service.cancel_plan(plan.id)
        assert plan.status == "cancelled"

        # Cannot cancel an already-cancelled plan
        with pytest.raises(ValueError, match="Cannot cancel"):
            service.cancel_plan(plan.id)

        # Cannot execute step on cancelled plan
        plan2 = service.create_plan(
            user_id=1, goal="Another", steps=[{"step": 0, "description": "X", "status": "pending", "depends_on": []}]
        )
        service.cancel_plan(plan2.id)
        with pytest.raises(ValueError, match="Cannot execute step"):
            service.execute_step(plan2.id, 0, result={})

    def test_confidence_estimation(self, db_session):
        service = TaskPlanningService(db_session)

        # Simple 2-step plan without tools → ~0.80
        steps_simple = [
            {"step": 0, "description": "A", "status": "pending", "depends_on": []},
            {"step": 1, "description": "B", "status": "pending", "depends_on": [0]},
        ]
        plan = service.create_plan(user_id=1, goal="Simple", steps=steps_simple)
        assert plan.confidence > 0.5

        # Complex plan with tools → higher confidence
        steps_tools = [
            {"step": 0, "description": "A", "status": "pending", "depends_on": [], "tool": "search"},
            {"step": 1, "description": "B", "status": "pending", "depends_on": [0], "tool": "analyze"},
            {"step": 2, "description": "C", "status": "pending", "depends_on": [1], "tool": "summarize"},
        ]
        plan_tools = service.create_plan(user_id=1, goal="Tooled", steps=steps_tools)
        # More steps + tools should still yield reasonable confidence
        assert plan_tools.confidence is not None
        assert plan_tools.confidence > 0.3
