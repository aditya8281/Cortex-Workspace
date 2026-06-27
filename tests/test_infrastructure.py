"""Meta-tests that verify the test infrastructure itself works."""

import pytest
from tests.factories.memory_factories import create_document, create_document_batch
from tests.mocks.llm_mocks import create_mock_llm_response, create_mock_llm_client, create_mock_redis, create_mock_qdrant
from tests.mocks.agent_mocks import MockTool, MockAgentLoop, create_agent_response, create_tool_call, create_tool_result
from tests.mocks.http_mocks import create_mock_http_response, create_mock_http_client


class TestFactoryInfrastructure:
    """Verify factory functions produce valid objects."""

    def test_create_document_returns_valid_model(self):
        doc = create_document()
        assert doc.id is not None
        assert doc.filename is not None
        assert doc.path is not None

    def test_create_document_accepts_overrides(self):
        doc = create_document(filename="custom.md")
        assert doc.filename == "custom.md"

    def test_batch_factory_creates_correct_count(self):
        docs = create_document_batch(10)
        assert len(docs) == 10
        assert len(set(d.id for d in docs)) == 10


class TestMockInfrastructure:
    """Verify mock objects work correctly."""

    def test_mock_llm_response_structure(self):
        response = create_mock_llm_response(content="Test")
        assert "choices" in response
        assert response["choices"][0]["message"]["content"] == "Test"

    def test_mock_llm_client_has_methods(self):
        client = create_mock_llm_client()
        assert hasattr(client.chat.completions, "create")

    @pytest.mark.asyncio
    async def test_mock_redis_returns_none_by_default(self):
        redis = create_mock_redis()
        result = await redis.get("key")
        assert result is None

    def test_mock_qdrant_returns_empty_list(self):
        qdrant = create_mock_qdrant()
        result = qdrant.search("collection", [1, 2, 3])
        assert result == []

    def test_mock_http_response(self):
        response = create_mock_http_response(200, {"data": "test"})
        assert response.status_code == 200
        assert response.json() == {"data": "test"}

    def test_agent_response_with_content(self):
        response = create_agent_response(content="Hello")
        assert response["choices"][0]["message"]["content"] == "Hello"

    def test_agent_response_with_tool_calls(self):
        tool_call = create_tool_call("search", {"query": "test"})
        response = create_agent_response(tool_calls=[tool_call])
        assert len(response["choices"][0]["message"]["tool_calls"]) == 1

    def test_tool_result(self):
        result = create_tool_result("call_001", "Result text")
        assert result["tool_call_id"] == "call_001"
        assert result["content"] == "Result text"

    @pytest.mark.asyncio
    async def test_mock_tool_execution(self):
        tool = MockTool("test_tool", result="success")
        result = await tool.execute(input="data")
        assert result == {"result": "success"}
        assert tool.call_count == 1

    @pytest.mark.asyncio
    async def test_mock_tool_error(self):
        tool = MockTool("failing_tool", error="Something went wrong")
        result = await tool.execute()
        assert result == {"error": "Something went wrong"}

    @pytest.mark.asyncio
    async def test_mock_agent_loop(self):
        loop = MockAgentLoop()
        loop.add_llm_response(create_agent_response(content="Step 1"))
        loop.add_llm_response(create_agent_response(content="Step 2"))

        result1 = await loop.execute_step()
        assert result1["choices"][0]["message"]["content"] == "Step 1"

        result2 = await loop.execute_step()
        assert result2["choices"][0]["message"]["content"] == "Step 2"

        result3 = await loop.execute_step()
        assert result3 == {"done": True}
