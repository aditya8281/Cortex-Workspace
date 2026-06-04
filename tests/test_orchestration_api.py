import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.db.base import Base
from backend.app.api.deps import get_db


@pytest.fixture(name="db_session", scope="function")
def fixture_db_session(tmp_path):
    db_file = tmp_path / "test_orchestration_api.db"
    db_url = f"sqlite:///{db_file}"

    test_engine = create_engine(db_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()


@pytest.fixture(name="client", scope="function")
def fixture_client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_route_task(client):
    # Test routing a coding query
    response = client.post(
        "/api/v1/sync/orchestration/route_task",
        json={"query": "write a python function to add two numbers"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "agent_selected" in data
    assert "confidence" in data
    assert data["classified_task"] == "Coding"

    # Test routing a chat query
    response = client.post(
        "/api/v1/sync/orchestration/route_task",
        json={"query": "hello there! how are you?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["classified_task"] == "Chat"


@pytest.mark.asyncio
async def test_execute_agent(client):
    # Mock route_and_generate in IntelligentRouter
    with patch(
        "backend.app.ai.intelligent_router.IntelligentRouter.route_and_generate",
        new_callable=AsyncMock
    ) as mock_route:
        mock_route.return_value = {
            "response": "Hello! I am ready to assist you.",
            "routing_info": {
                "model_used": "mock-llm",
                "provider": "Mock",
                "response_time": 0.01,
                "selection_reason": "test"
            }
        }

        payload = {
            "agent_name": "ChatAgent",
            "query": "hello",
            "context": "System context"
        }
        response = client.post("/api/v1/sync/orchestration/execute_agent", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["agent_name"] == "ChatAgent"
        assert data["result"] == "Hello! I am ready to assist you."
        assert data["confidence"] > 0.0
        assert "reasoning_summary" in data


@pytest.mark.asyncio
async def test_run_task(client):
    # Mock route_and_generate for primary agent execution
    # And mock claims verification check inside VerificationAgent
    with patch(
        "backend.app.ai.intelligent_router.IntelligentRouter.route_and_generate",
        new_callable=AsyncMock
    ) as mock_route:
        mock_route.return_value = {
            "response": "Here is the plan to write the addition function.",
            "routing_info": {
                "model_used": "mock-llm",
                "provider": "Mock",
                "response_time": 0.05,
                "selection_reason": "test"
            }
        }

        # Run a coding/planning task that triggers multi-agent execution graph
        payload = {
            "query": "create a layout checklist for planning the coding steps",
            "history": []
        }
        response = client.post("/api/v1/sync/orchestration/run_task", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "response" in data
        assert "trace" in data
        assert "execution_order" in data["trace"]


def test_debug_execution_graph(client):
    # Test debug_execution_graph query routing for coding task class
    response = client.get(
        "/api/v1/sync/orchestration/debug_execution_graph?query=write code for authentication"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["classified_task"] == "Coding"
    assert data["agent_selected"] == "CodingAgent"
    assert "graph_structure" in data
    nodes = data["graph_structure"]["nodes"]
    # Coding task class graph structure must contain RepositoryAgent, SearchAgent, CodingAgent, and VerificationAgent
    agent_names = {node["agent_name"] for node in nodes}
    assert "RepositoryAgent" in agent_names
    assert "SearchAgent" in agent_names
    assert "CodingAgent" in agent_names
    assert "VerificationAgent" in agent_names
