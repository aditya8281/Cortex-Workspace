import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.ai.gateway import AIGateway


@pytest.fixture(name="gateway")
def fixture_gateway():
    return AIGateway()


@pytest.mark.asyncio
async def test_ai_gateway_file_search_agent(gateway):
    query = "Search my python files"
    response = await gateway.route(query)
    assert "FileSearchAgent" in response.answer


@pytest.mark.asyncio
async def test_ai_gateway_system_scanner_agent(gateway):
    query = "Check database errors"
    response = await gateway.route(query)
    assert "SystemScanner" in response.answer


@pytest.mark.asyncio
async def test_ai_gateway_llm_routing_and_memory(gateway):
    query = "What is the capital of France?"

    with patch(
        "backend.app.ai.intelligent_router.IntelligentRouter.route_and_generate",
        new_callable=AsyncMock,
    ) as mock_route:
        mock_route.return_value = {"response": "Paris", "routing_info": None}

        # 1. First query with user_id: Memory is empty, so it should call LLM and save response.
        response = await gateway.route(query, user_id=42)
        assert "Paris" in response.answer
        mock_route.assert_called_once()

        # 2. Second query with same keywords: Memory recall context is passed to LLM.
        mock_route.reset_mock()
        mock_route.return_value = {"response": "Paris recall response", "routing_info": None}
        recall_response = await gateway.route("France capital", user_id=42)
        assert "[Memory Recall]" in recall_response.answer
        assert "Paris" in recall_response.answer
        mock_route.assert_called_once()


def test_ai_api_endpoints():
    client = TestClient(app)

    # 1. Test public ask endpoint
    with patch("backend.app.ai.llm_router.LLMRouter.generate", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = "Artificial Intelligence"
        payload = {"query": "Tell me about AI"}

        response = client.post("/api/v1/ai/ask", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "Tell me about AI"
        assert "Artificial Intelligence" in data["response"]
        assert "execution_id" in data
        assert data["user_id"] is None

    # 2. Test chat endpoint without token (should return 401)
    response = client.post("/api/v1/ai/chat", json={"query": "hello"})
    assert response.status_code == 401
