import sys
import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import numpy as np


class MockSentenceTransformer:

    def __init__(self, *args, **kwargs):
        pass

    def encode(self, texts, *args, **kwargs):
        return np.random.rand(len(texts), 384).tolist()


# Mock sentence_transformers module at import time to prevent real downloads/loading
mock_module = MagicMock()
mock_module.SentenceTransformer = MockSentenceTransformer
sys.modules["sentence_transformers"] = mock_module


@pytest.fixture(autouse=True)
def mock_llm_router_generate():
    from backend.app.ai.llm_router import LLMRouter
    from backend.app.rag.service import RAGService
    
    async def mock_generate(self, prompt, system_prompt=None, model=None, inference_engine=None, api_key=None, api_base_url=None):
        from backend.app.ai.intelligent_router import IntelligentRouter
        import unittest.mock
        
        # Check if IntelligentRouter.route_and_generate is mocked/patched in current test
        route_mock = IntelligentRouter.route_and_generate
        if isinstance(route_mock, (unittest.mock.Mock, unittest.mock.MagicMock, AsyncMock)):
            # Call the mock to update call_count / call_args and execute side_effect if any
            if asyncio.iscoroutinefunction(route_mock) or isinstance(route_mock, AsyncMock):
                val = await route_mock(prompt)
            else:
                val = route_mock(prompt)
                
            if isinstance(val, dict) and "response" in val:
                return val["response"]
            if isinstance(val, str):
                return val

        prompt_lower = prompt.lower()
        if "france" in prompt_lower or "paris" in prompt_lower:
            return "Paris"
        if "caching" in prompt_lower:
            return "Caching is storing copies of data."
        if "filesearchagent" in prompt_lower or "search my python files" in prompt_lower:
            return "I ran FileSearchAgent and found nothing."
        if "systemscanner" in prompt_lower or "check database errors" in prompt_lower:
            return "I ran SystemScanner and found no errors."
        if "tell me about ai" in prompt_lower:
            return "Artificial Intelligence"
            
        return "Mock LLM Response"
        
    orig_search = RAGService.search
    async def mock_rag_search(self, query, top_k=5, embedding_model=None, vector_db=None, code_parsing=None):
        if getattr(self, "_bypass_mock", False):
            return await orig_search(self, query, top_k, embedding_model, vector_db, code_parsing)
        return []

    with patch.object(LLMRouter, "generate", mock_generate), \
         patch.object(RAGService, "search", mock_rag_search):
        yield

