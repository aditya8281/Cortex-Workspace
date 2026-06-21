from unittest.mock import AsyncMock, patch

HEADERS = {"Authorization": "Bearer fake-token"}


def test_list_agents_empty(client, mock_auth):
    resp = client.get("/api/v1/agents")
    assert resp.status_code == 200
    data = resp.json()
    assert data["agents"] == []


def test_create_agent(client, mock_auth):
    resp = client.post(
        "/api/v1/agents",
        json={
            "name": "Test Agent",
            "system_prompt": "You are a test agent.",
            "model_id": "local",
            "description": "A test",
        },
        headers=HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "created"
    agent = data["agent"]
    assert agent["name"] == "Test Agent"
    assert agent["system_prompt"] == "You are a test agent."
    assert agent["model_id"] == "local"
    assert agent["is_active"] is True
    assert "id" in agent


def test_get_agent(client, mock_auth, db_session):
    from backend.app.models.agent import Agent

    agent = Agent(
        user_id=mock_auth.id,
        name="Fetch Me",
        system_prompt="prompt",
        model_id="local",
    )
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)

    resp = client.get(f"/api/v1/agents/{agent.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent"]["id"] == agent.id
    assert data["agent"]["name"] == "Fetch Me"


def test_get_agent_not_found(client, mock_auth):
    resp = client.get("/api/v1/agents/99999")
    assert resp.status_code == 404


def test_update_agent(client, mock_auth, db_session):
    from backend.app.models.agent import Agent

    agent = Agent(
        user_id=mock_auth.id,
        name="Old Name",
        system_prompt="old prompt",
        model_id="local",
    )
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)

    resp = client.put(
        f"/api/v1/agents/{agent.id}",
        json={"name": "New Name", "system_prompt": "new prompt"},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "updated"

    resp2 = client.get(f"/api/v1/agents/{agent.id}")
    assert resp2.json()["agent"]["name"] == "New Name"
    assert resp2.json()["agent"]["system_prompt"] == "new prompt"


def test_delete_agent(client, mock_auth, db_session):
    from backend.app.models.agent import Agent

    agent = Agent(
        user_id=mock_auth.id,
        name="Delete Me",
        system_prompt="prompt",
        model_id="local",
    )
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)

    resp = client.delete(f"/api/v1/agents/{agent.id}", headers=HEADERS)
    assert resp.status_code == 200

    resp2 = client.get(f"/api/v1/agents/{agent.id}")
    assert resp2.status_code == 404


def test_delete_agent_not_found(client, mock_auth):
    resp = client.delete("/api/v1/agents/99999", headers=HEADERS)
    assert resp.status_code == 404


@patch("backend.app.agents.background.run_agent_background", new_callable=AsyncMock)
def test_create_run(mock_bg, client, mock_auth, db_session):
    from backend.app.models.agent import Agent

    agent = Agent(
        user_id=mock_auth.id,
        name="Run Agent",
        system_prompt="prompt",
        model_id="local",
    )
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)

    resp = client.post(
        "/api/v1/agents/runs",
        json={"agent_id": agent.id, "input": "Do something"},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "started"
    assert "run_id" in data


def test_list_runs(client, mock_auth, db_session):
    from backend.app.models.agent import Agent, AgentRun

    agent = Agent(
        user_id=mock_auth.id,
        name="List Runs Agent",
        system_prompt="prompt",
        model_id="local",
    )
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)

    run = AgentRun(
        agent_id=agent.id,
        user_id=1,
        input_text="test input",
        status="completed",
    )
    db_session.add(run)
    db_session.commit()

    resp = client.get("/api/v1/agents/runs")
    assert resp.status_code == 200
    runs = resp.json()["runs"]
    assert len(runs) >= 1
    assert runs[0]["input"] == "test input"


def test_get_run(client, mock_auth, db_session):
    from backend.app.models.agent import Agent, AgentRun

    agent = Agent(
        user_id=mock_auth.id,
        name="Get Run Agent",
        system_prompt="prompt",
        model_id="local",
    )
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)

    run = AgentRun(
        agent_id=agent.id,
        user_id=1,
        input_text="get me",
        status="completed",
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)

    resp = client.get(f"/api/v1/agents/runs/{run.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["run"]["id"] == run.id
    assert data["run"]["input"] == "get me"
    assert isinstance(data["steps"], list)


def test_get_run_not_found(client, mock_auth):
    resp = client.get("/api/v1/agents/runs/99999")
    assert resp.status_code == 404


def test_get_run_steps(client, mock_auth, db_session):
    from backend.app.models.agent import Agent, AgentRun, AgentStep

    agent = Agent(
        user_id=mock_auth.id,
        name="Steps Agent",
        system_prompt="prompt",
        model_id="local",
    )
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)

    run = AgentRun(
        agent_id=agent.id,
        user_id=1,
        input_text="steps input",
        status="completed",
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)

    step = AgentStep(
        run_id=run.id,
        step_number=1,
        action="think",
        status="completed",
        observation="thought result",
    )
    db_session.add(step)
    db_session.commit()

    resp = client.get(f"/api/v1/agents/runs/{run.id}/steps")
    assert resp.status_code == 200
    steps = resp.json()["steps"]
    assert len(steps) == 1
    assert steps[0]["action"] == "think"
    assert steps[0]["step_number"] == 1
