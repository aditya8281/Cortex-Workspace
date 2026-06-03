import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.app.core.redis import RedisCache
from backend.app.executor.graph_runner import GraphRunner
from backend.app.rag.service import RAGService

class MockRedisClient:
    def __init__(self):
        self.store = {}

    async def ping(self):
        return True

    async def get(self, key):
        return self.store.get(key)

    async def set(self, key, value, ex=None):
        self.store[key] = str(value)
        return True

    async def delete(self, *keys):
        for k in keys:
            if k in self.store:
                del self.store[k]
        return True

    async def keys(self, pattern):
        clean_pat = pattern.replace("*", "")
        return [k for k in self.store.keys() if clean_pat in k]

    async def aclose(self):
        pass


@pytest.fixture
def mock_redis():
    mock_client = MockRedisClient()
    with patch("redis.asyncio.from_url", return_value=mock_client):
        # Patch the global redis_cache client
        with patch("backend.app.core.redis.redis_cache.client", mock_client):
            with patch("backend.app.core.redis.redis_cache._connected", True):
                yield mock_client


@pytest.mark.asyncio
async def test_redis_cache_operations(mock_redis):
    cache = RedisCache(redis_url="redis://localhost:6379/9")
    cache.client = mock_redis
    cache._connected = True
    
    # Test ping
    connected = await cache.ping()
    assert connected is True

    # Test set and get
    set_ok = await cache.set("test_key", {"status": "ok"}, expire_seconds=10)
    assert set_ok is True
    assert mock_redis.store["test_key"] == '{"status": "ok"}'

    val = await cache.get("test_key")
    assert val == {"status": "ok"}

    # Test delete
    del_ok = await cache.delete("test_key")
    assert del_ok is True
    assert "test_key" not in mock_redis.store

    # Test clear_pattern
    await cache.set("prefix:one", "1")
    await cache.set("prefix:two", "2")
    await cache.set("other:three", "3")

    clear_ok = await cache.clear_pattern("prefix:*")
    assert clear_ok is True
    assert "prefix:one" not in mock_redis.store
    assert "prefix:two" not in mock_redis.store
    assert "other:three" in mock_redis.store


@pytest.mark.asyncio
async def test_llm_response_caching_hit(mock_redis):
    # Setup mock executor
    mock_executor = MagicMock()
    mock_executor.llm.generate = AsyncMock()
    # IntelligentRouter is used on cache-miss; provide an async mock
    mock_executor.router.route_and_generate = AsyncMock(return_value={
        "response": "Router LLM Answer",
        "routing_info": None,
    })

    runner = GraphRunner(mock_executor)

    import json
    cached_payload = json.dumps({"response": "Cached LLM Answer", "routing_info": None})
    # Mock redis_cache.get directly
    from backend.app.core.redis import redis_cache
    with patch.object(redis_cache, "get", AsyncMock(return_value=cached_payload)):
        state = {
            "intent": MagicMock(intent="chat"),
            "history": [],
            "tools": [],
            "memory": None,
        }

        # Patch compiler
        with patch("backend.app.executor.context_compiler.ContextCompiler.compile", return_value="some prompt"):
            response = await runner._run_llm(state, "hello", user_id=None)

        # Check cache hit bypasses generate
        assert response == "Cached LLM Answer"
        mock_executor.llm.generate.assert_not_called()


@pytest.mark.asyncio
async def test_rag_search_caching_hit(mock_redis):
    service = RAGService(repo_path=".")
    
    cached_payload = [{"data": {"chunk": "Cached code line"}, "score": 0.1}]
    
    from backend.app.core.redis import redis_cache
    with patch.object(redis_cache, "get", AsyncMock(return_value=cached_payload)):
        # Mock retriever build
        mock_retriever = MagicMock()
        service._get_retriever = MagicMock(return_value=mock_retriever)

        # Run search
        results = await service.search("test query")
        
        assert results == cached_payload
        mock_retriever.retrieve.assert_not_called()
