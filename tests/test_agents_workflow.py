"""Tests for agent workflow endpoints: runs, steps, feedback, metrics."""

from unittest.mock import patch

from backend.app.models.agent import Agent, AgentFeedback, AgentRun, AgentStep

HEADERS = {"Authorization": "Bearer fake-token"}


# ── Helpers ────────────────────────────────────────────────────


def _create_agent(db_session, user_id=1):
    agent = Agent(
        user_id=user_id,
        name="Workflow Agent",
        system_prompt="prompt",
        model_id="local",
    )
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)
    return agent


def _create_run(db_session, agent_id, user_id=1, status="completed"):
    run = AgentRun(
        agent_id=agent_id,
        user_id=user_id,
        input_text="test input",
        status=status,
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)
    return run


def _create_step(db_session, run_id, step_number=1, action="think"):
    step = AgentStep(
        run_id=run_id,
        step_number=step_number,
        action=action,
        status="completed",
        observation="done",
    )
    db_session.add(step)
    db_session.commit()
    db_session.refresh(step)
    return step


def _create_feedback(db_session, run_id, user_id=1, rating=4, comment="good"):
    feedback = AgentFeedback(
        run_id=run_id,
        user_id=user_id,
        rating=rating,
        comment=comment,
    )
    db_session.add(feedback)
    db_session.commit()
    db_session.refresh(feedback)
    return feedback


# ── Tests ──────────────────────────────────────────────────────


class TestGetRunStatus:
    def test_run_status_unknown_for_db_only_run(self, client, mock_auth, db_session):
        """A run created directly in DB (not via background task) returns 'unknown'."""
        agent = _create_agent(db_session)
        run = _create_run(db_session, agent.id)

        resp = client.get(f"/api/v1/agents/runs/{run.id}/status", headers=HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["run_id"] == run.id
        assert data["status"] == "unknown"

    def test_run_status_running(self, client, mock_auth, db_session):
        """A run that is actively tracked returns 'running'."""
        agent = _create_agent(db_session)
        run = _create_run(db_session, agent.id)

        import backend.app.agents.background as bg
        mock_task = type("MockTask", (), {"done": lambda self: False})()
        bg._active_runs[run.id] = mock_task
        try:
            resp = client.get(f"/api/v1/agents/runs/{run.id}/status", headers=HEADERS)
            assert resp.status_code == 200
            assert resp.json()["status"] == "running"
        finally:
            bg._active_runs.pop(run.id, None)

    def test_run_status_not_found(self, client, mock_auth):
        resp = client.get("/api/v1/agents/runs/99999/status", headers=HEADERS)
        assert resp.status_code == 404


class TestAddFeedback:
    def test_add_feedback(self, client, mock_auth, db_session):
        agent = _create_agent(db_session)
        run = _create_run(db_session, agent.id)

        resp = client.post(
            f"/api/v1/agents/runs/{run.id}/feedback",
            json={"rating": 4, "comment": "good"},
            headers=HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "created"
        assert data["feedback"]["rating"] == 4
        assert data["feedback"]["comment"] == "good"
        assert "id" in data["feedback"]

    def test_add_feedback_no_comment(self, client, mock_auth, db_session):
        agent = _create_agent(db_session)
        run = _create_run(db_session, agent.id)

        resp = client.post(
            f"/api/v1/agents/runs/{run.id}/feedback",
            json={"rating": 5},
            headers=HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["feedback"]["rating"] == 5
        assert data["feedback"]["comment"] is None

    def test_add_feedback_invalid_rating(self, client, mock_auth, db_session):
        agent = _create_agent(db_session)
        run = _create_run(db_session, agent.id)

        resp = client.post(
            f"/api/v1/agents/runs/{run.id}/feedback",
            json={"rating": 6, "comment": "too high"},
            headers=HEADERS,
        )
        assert resp.status_code == 422

    def test_add_feedback_run_not_found(self, client, mock_auth):
        resp = client.post(
            "/api/v1/agents/runs/99999/feedback",
            json={"rating": 3, "comment": "no run"},
            headers=HEADERS,
        )
        assert resp.status_code == 404


class TestGetFeedback:
    def test_list_feedback(self, client, mock_auth, db_session):
        agent = _create_agent(db_session)
        run = _create_run(db_session, agent.id)
        _create_feedback(db_session, run.id, rating=5, comment="excellent")
        _create_feedback(db_session, run.id, rating=3, comment="ok")

        resp = client.get(f"/api/v1/agents/runs/{run.id}/feedback", headers=HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["feedback"]) == 2
        assert data["feedback"][0]["rating"] == 5
        assert data["feedback"][1]["rating"] == 3

    def test_list_feedback_empty(self, client, mock_auth, db_session):
        agent = _create_agent(db_session)
        run = _create_run(db_session, agent.id)

        resp = client.get(f"/api/v1/agents/runs/{run.id}/feedback", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["feedback"] == []

    def test_list_feedback_run_not_found(self, client, mock_auth):
        resp = client.get("/api/v1/agents/runs/99999/feedback", headers=HEADERS)
        assert resp.status_code == 404


class TestAgentMetrics:
    def test_metrics_empty(self, client, mock_auth):
        resp = client.get("/api/v1/agents/metrics", headers=HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_runs"] == 0
        assert data["success_rate"] == 0.0
        assert data["avg_duration_seconds"] is None
        assert data["total_steps"] == 0
        assert data["avg_steps_per_run"] == 0.0
        assert data["feedback_summary"]["count"] == 0

    def test_metrics_with_runs(self, client, mock_auth, db_session):
        from datetime import datetime, timezone

        agent = _create_agent(db_session)
        run1 = _create_run(db_session, agent.id, status="completed")
        run1.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
        run1.completed_at = datetime(2025, 1, 1, 0, 0, 10, tzinfo=timezone.utc)
        _create_run(db_session, agent.id, status="failed")
        db_session.commit()

        _create_step(db_session, run1.id, step_number=1, action="think")
        _create_step(db_session, run1.id, step_number=2, action="act")
        _create_feedback(db_session, run1.id, rating=5, comment="great")

        resp = client.get("/api/v1/agents/metrics", headers=HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_runs"] == 2
        assert data["success_rate"] == 0.5
        assert data["total_steps"] == 2
        assert data["avg_steps_per_run"] == 1.0
        assert data["feedback_summary"]["count"] == 1
        assert data["feedback_summary"]["avg_rating"] == 5.0


class TestGetRunStepsNotFound:
    def test_steps_run_not_found(self, client, mock_auth):
        resp = client.get("/api/v1/agents/runs/99999/steps", headers=HEADERS)
        assert resp.status_code == 404


class TestCreateRunInvalidAgent:
    def test_create_run_invalid_agent_id(self, client, mock_auth, db_session):
        """When the agent doesn't exist, create_run raises ValueError -> 404."""
        from backend.app.agents.run_manager import AgentRunManager

        original_create = AgentRunManager.create_run

        def patched_create(self, agent_id, user_id, input_text):
            agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
            if not agent:
                raise ValueError(f"Agent {agent_id} not found")
            return original_create(self, agent_id, user_id, input_text)

        with patch.object(AgentRunManager, "create_run", patched_create):
            resp = client.post(
                "/api/v1/agents/runs",
                json={"agent_id": 99999, "input": "do something"},
                headers=HEADERS,
            )
            assert resp.status_code == 404
            assert "not found" in resp.json()["detail"].lower()
