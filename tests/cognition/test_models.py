"""Tests for cognition and execution models."""

from backend.app.models.cognition.confidence_score import ConfidenceScore
from backend.app.models.cognition.error_analysis import ErrorAnalysis
from backend.app.models.cognition.hypothesis import Hypothesis
from backend.app.models.cognition.task_plan import TaskPlan
from backend.app.models.execution.tool_execution import ToolExecution
from backend.app.models.execution.workflow import Workflow


class TestTaskPlanModel:
    def test_create_plan(self, db_session):
        plan = TaskPlan(
            user_id=1,
            goal="Build a feature",
            steps=[
                {"step": 0, "description": "Analyze", "status": "pending", "depends_on": []},
                {"step": 1, "description": "Implement", "status": "pending", "depends_on": [0]},
            ],
            status="pending",
            confidence=0.7,
        )
        db_session.add(plan)
        db_session.commit()
        assert plan.id is not None
        assert len(plan.steps) == 2
        assert plan.confidence == 0.7

    def test_plan_defaults(self, db_session):
        plan = TaskPlan(user_id=1, goal="Test", steps=[])
        db_session.add(plan)
        db_session.commit()
        assert plan.status == "pending"
        assert plan.current_step == 0
        assert plan.steps == []

    def test_plan_indexes(self, db_session):
        """Verify composite indexes are defined."""
        table = TaskPlan.__table__
        index_names = {idx.name for idx in table.indexes}
        assert "ix_task_plan_user_status" in index_names
        assert "ix_task_plan_user_created" in index_names


class TestErrorAnalysisModel:
    def test_create_analysis(self, db_session):
        analysis = ErrorAnalysis(
            user_id=1,
            error_type="ValueError",
            error_message="Invalid input",
            fingerprint="ValueError:invalid_input",
            context={"module": "test"},
            severity="error",
        )
        db_session.add(analysis)
        db_session.commit()
        assert analysis.id is not None
        assert analysis.fingerprint == "ValueError:invalid_input"

    def test_fingerprint_grouping(self, db_session):
        """Verify fingerprint enables pattern matching queries."""
        for fp in ["ValueError:input", "ValueError:input", "TypeError:conversion"]:
            db_session.add(ErrorAnalysis(user_id=1, error_type="Error", fingerprint=fp))
        db_session.commit()
        from sqlalchemy import func

        counts = db_session.query(ErrorAnalysis.fingerprint, func.count()).group_by(ErrorAnalysis.fingerprint).all()
        assert len(counts) == 2

    def test_defaults(self, db_session):
        analysis = ErrorAnalysis(user_id=1, error_type="RuntimeError")
        db_session.add(analysis)
        db_session.commit()
        assert analysis.severity == "info"
        assert analysis.resolved == 0


class TestHypothesisModel:
    def test_create_hypothesis(self, db_session):
        hypo = Hypothesis(
            user_id=1,
            hypothesis="Feature X causes bug Y",
            evidence_for=[{"text": "Log shows X before Y", "weight": 1.0}],
            evidence_against=[],
            confidence=0.7,
            status="active",
        )
        db_session.add(hypo)
        db_session.commit()
        assert hypo.id is not None
        assert hypo.confidence == 0.7
        assert hypo.status == "active"

    def test_defaults(self, db_session):
        hypo = Hypothesis(user_id=1, hypothesis="Test")
        db_session.add(hypo)
        db_session.commit()
        assert hypo.evidence_for == []
        assert hypo.evidence_against == []
        assert hypo.status == "active"
        assert hypo.confidence == 0.5

    def test_indexes(self, db_session):
        table = Hypothesis.__table__
        index_names = {idx.name for idx in table.indexes}
        assert "ix_hypothesis_user_status" in index_names
        assert "ix_hypothesis_user_confidence" in index_names


class TestConfidenceScoreModel:
    def test_create_score(self, db_session):
        score = ConfidenceScore(
            user_id=1,
            task_type="planning",
            confidence=0.75,
            factors=[{"key": "past_successes", "value": 5, "weight": 1.0}],
            context={"goal": "test"},
        )
        db_session.add(score)
        db_session.commit()
        assert score.id is not None
        assert score.task_type == "planning"
        assert score.confidence == 0.75


class TestToolExecutionModel:
    def test_create_execution(self, db_session):
        exec_ = ToolExecution(
            user_id=1,
            tool_name="doubler",
            parameters={"x": 5},
            status="running",
        )
        db_session.add(exec_)
        db_session.commit()
        assert exec_.id is not None
        assert exec_.status == "running"
        assert exec_.retry_count == 0

    def test_defaults(self, db_session):
        exec_ = ToolExecution(user_id=1, tool_name="echo")
        db_session.add(exec_)
        db_session.commit()
        assert exec_.status == "pending"
        assert exec_.retry_count == 0
        assert exec_.parameters is None
        assert exec_.result is None


class TestWorkflowModel:
    def test_create_workflow(self, db_session):
        wf = Workflow(
            user_id=1,
            name="Test Workflow",
            steps=[
                {"tool": "echo", "params": {"msg": "hi"}},
                {"tool": "echo", "params": {"msg": "bye"}},
            ],
            status="idle",
        )
        db_session.add(wf)
        db_session.commit()
        assert wf.id is not None
        assert wf.run_count == 0
        assert wf.status == "idle"

    def test_defaults(self, db_session):
        wf = Workflow(user_id=1, name="Empty WF", steps=[])
        db_session.add(wf)
        db_session.commit()
        assert wf.status == "idle"
        assert wf.current_step == 0
        assert wf.run_count == 0
