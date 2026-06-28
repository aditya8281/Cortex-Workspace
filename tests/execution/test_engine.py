"""Tests for ExecutionEngine and WorkflowOrchestrator."""

import pytest

from backend.app.services.execution.engine import ExecutionEngine
from backend.app.services.execution.tool_registry import ToolRegistry


def _make_registry():
    registry = ToolRegistry()

    def doubler(x: int = 1):
        return {"result": x * 2}

    def failing():
        raise RuntimeError("Tool failed")

    def echo(message: str = "ok"):
        return {"echo": message}

    def add(a: int = 0, b: int = 0):
        return {"result": a + b}

    registry.register("doubler", doubler, "Doubles", {"x": {"type": "integer"}})
    registry.register("failing", failing, "Fails", {})
    registry.register("echo", echo, "Echo", {"message": {"type": "string"}})
    registry.register(
        "add",
        add,
        "Add",
        {
            "a": {"type": "integer"},
            "b": {"type": "integer"},
        },
    )
    return registry


class TestExecutionEngine:
    @pytest.fixture
    def engine(self, db_session):
        return ExecutionEngine(db_session, _make_registry())

    def test_execute_success(self, engine):
        execution = engine.execute_tool(user_id=1, tool_name="doubler", params={"x": 5})
        assert execution.status == "success"
        assert execution.result == {"result": 10}
        assert execution.duration_ms is not None

    def test_execute_failure(self, engine):
        execution = engine.execute_tool(user_id=1, tool_name="failing", params={})
        assert execution.status == "failed"
        assert "Tool failed" in execution.error_message

    def test_execute_blocked(self, engine):
        engine.verifier.add_rule("block_all", lambda t, p, c: False, "Block all")
        execution = engine.execute_tool(user_id=1, tool_name="doubler", params={"x": 1})
        assert execution.status == "blocked"

    def test_execution_stats(self, engine):
        engine.execute_tool(user_id=1, tool_name="doubler", params={"x": 1})
        engine.execute_tool(user_id=1, tool_name="doubler", params={"x": 2})
        engine.execute_tool(user_id=1, tool_name="failing", params={})

        stats = engine.get_execution_stats(1)
        assert stats["total"] == 3
        assert stats["successful"] == 2
        assert stats["failed"] == 1
        assert stats["success_rate"] == pytest.approx(66.67, abs=1)

    def test_execute_with_retry(self, engine):
        execution = engine.execute_with_retry(user_id=1, tool_name="failing", params={}, max_retries=2)
        assert execution.status == "failed"

    def test_execute_tool_not_found(self, engine):
        execution = engine.execute_tool(user_id=1, tool_name="nonexistent", params={})
        assert execution.status == "failed"
        assert "not registered" in execution.error_message

    def test_get_execution(self, engine):
        created = engine.execute_tool(user_id=1, tool_name="doubler", params={"x": 3})
        fetched = engine.get_execution(created.id)
        assert fetched is not None
        assert fetched.id == created.id

    def test_get_user_executions(self, engine):
        engine.execute_tool(user_id=1, tool_name="doubler", params={"x": 1})
        engine.execute_tool(user_id=2, tool_name="doubler", params={"x": 2})
        user1 = engine.get_user_executions(user_id=1)
        assert len(user1) == 1
        assert user1[0].user_id == 1

    def test_tool_breakdown(self, engine):
        engine.execute_tool(user_id=1, tool_name="doubler", params={"x": 1})
        engine.execute_tool(user_id=1, tool_name="doubler", params={"x": 2})
        engine.execute_tool(user_id=1, tool_name="echo", params={"message": "hi"})
        stats = engine.get_execution_stats(1)
        assert stats["tool_breakdown"]["doubler"] == 2
        assert stats["tool_breakdown"]["echo"] == 1


class TestWorkflowOrchestrator:
    @pytest.fixture
    def orchestrator(self, db_session):
        from backend.app.services.execution.workflow import WorkflowOrchestrator

        engine = ExecutionEngine(db_session, _make_registry())
        return WorkflowOrchestrator(db_session, engine)

    def test_create_workflow(self, orchestrator):
        steps = [
            {"tool": "echo", "params": {"message": "hello"}},
            {"tool": "echo", "params": {"message": "world"}, "depends_on": [0]},
        ]
        workflow = orchestrator.create_workflow(1, "Test WF", steps)
        assert workflow.name == "Test WF"
        assert workflow.status == "idle"
        assert len(workflow.steps) == 2

    def test_run_workflow(self, orchestrator):
        steps = [
            {"tool": "echo", "params": {"message": "step1"}},
            {"tool": "echo", "params": {"message": "step2"}},
        ]
        wf = orchestrator.create_workflow(1, "Run Test", steps)
        completed = orchestrator.run_workflow(wf.id)
        assert completed.status == "completed"
        assert completed.last_run is not None
        assert completed.run_count == 1

    def test_workflow_step_failure(self, orchestrator):
        steps = [
            {"tool": "echo", "params": {"message": "ok"}},
            {"tool": "nonexistent_tool", "params": {}},
        ]
        wf = orchestrator.create_workflow(1, "Fail Test", steps)
        failed = orchestrator.run_workflow(wf.id)
        assert failed.status == "failed"
        assert failed.error_message is not None

    def test_workflow_skip_on_failure(self, orchestrator):
        steps = [
            {"tool": "nonexistent_tool", "params": {}, "on_failure": "skip"},
            {"tool": "echo", "params": {"message": "after skip"}},
        ]
        wf = orchestrator.create_workflow(1, "Skip Test", steps)
        completed = orchestrator.run_workflow(wf.id)
        assert completed.status == "completed"
        assert completed.steps[0]["status"] == "skipped"

    def test_cycle_detection(self, orchestrator):
        steps = [
            {"tool": "echo", "params": {}, "depends_on": [1]},
            {"tool": "echo", "params": {}, "depends_on": [0]},
        ]
        with pytest.raises(ValueError, match="cycle"):
            orchestrator.create_workflow(1, "Cycle", steps)

    def test_cancel_workflow(self, orchestrator):
        wf = orchestrator.create_workflow(1, "Cancel", [{"tool": "echo", "params": {"message": "hi"}}])
        cancelled = orchestrator.cancel_workflow(wf.id)
        assert cancelled.status == "cancelled"

    def test_conditional_step(self, orchestrator):
        steps = [
            {"tool": "echo", "params": {"message": "first"}},
            {
                "tool": "echo",
                "params": {"message": "conditional"},
                "condition": {"type": "previous_step_success", "step_index": 0},
            },
        ]
        wf = orchestrator.create_workflow(1, "Conditional", steps)
        completed = orchestrator.run_workflow(wf.id)
        assert completed.steps[1]["status"] == "completed"

    def test_duplicate_workflow(self, orchestrator):
        wf = orchestrator.create_workflow(1, "Original", [{"tool": "echo", "params": {"message": "hi"}}])
        copy = orchestrator.duplicate_workflow(wf.id, "Copy")
        assert copy.name == "Copy"
        assert len(copy.steps) == len(wf.steps)

    def test_invalid_dep_index(self, orchestrator):
        steps = [{"tool": "echo", "params": {}, "depends_on": [5]}]
        with pytest.raises(ValueError, match="invalid index"):
            orchestrator.create_workflow(1, "Bad dep", steps)

    def test_missing_tool_field(self, orchestrator):
        steps = [{"params": {"message": "hi"}}]
        with pytest.raises(ValueError, match="missing 'tool'"):
            orchestrator.create_workflow(1, "No tool", steps)
