"""Tests for RAG-based tool selection — P05 Task 2."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock

from backend.app.agents.tools.selector import ToolSelector


class TestToolSelectorInit:
    def test_default_values(self):
        selector = ToolSelector()
        assert selector.top_k == 8
        assert selector.min_similarity == 0.3
        assert selector._tool_embeddings == {}

    def test_custom_values(self):
        selector = ToolSelector(top_k=5, min_similarity=0.5)
        assert selector.top_k == 5
        assert selector.min_similarity == 0.5


class TestToolSelectorIndexing:
    @pytest.mark.asyncio
    async def test_index_tools(self):
        mock_embedder = AsyncMock()
        mock_embedder.embed.return_value = [0.1, 0.2, 0.3]
        selector = ToolSelector(embedding_service=mock_embedder)
        tools = [
            {"function": {"name": "read_file", "description": "Read a file", "parameters": {}}},
            {"function": {"name": "write_file", "description": "Write a file", "parameters": {}}},
        ]
        await selector.index_tools(tools)
        assert "read_file" in selector._tool_embeddings
        assert "write_file" in selector._tool_embeddings

    @pytest.mark.asyncio
    async def test_index_empty_tools(self):
        selector = ToolSelector()
        await selector.index_tools([])
        assert selector._tool_embeddings == {}

    @pytest.mark.asyncio
    async def test_index_skips_no_description(self):
        selector = ToolSelector()
        tools = [{"function": {"name": "no_desc", "description": "", "parameters": {}}}]
        await selector.index_tools(tools)
        assert "no_desc" not in selector._tool_embeddings

    @pytest.mark.asyncio
    async def test_no_embedding_service_skips_indexing(self):
        selector = ToolSelector(embedding_service=None)
        tools = [{"function": {"name": "t", "description": "A tool", "parameters": {}}}]
        await selector.index_tools(tools)
        assert selector._tool_embeddings == {}


class TestToolSelectorSelection:
    @pytest.mark.asyncio
    async def test_select_tools_with_embeddings(self):
        mock_embedder = AsyncMock()
        call_count = 0

        async def embed_fn(text):
            nonlocal call_count
            call_count += 1
            if "read" in text.lower():
                return [1.0, 0.0, 0.0]
            elif "write" in text.lower():
                return [0.0, 1.0, 0.0]
            elif "file" in text.lower():
                return [0.8, 0.2, 0.0]
            return [0.0, 0.0, 1.0]

        mock_embedder.embed = AsyncMock(side_effect=embed_fn)

        selector = ToolSelector(embedding_service=mock_embedder, top_k=2, min_similarity=0.1)
        tools = [
            {"function": {"name": "read_file", "description": "Read a file from disk", "parameters": {}}},
            {"function": {"name": "write_file", "description": "Write content to a file", "parameters": {}}},
            {"function": {"name": "search_memory", "description": "Search long-term memory", "parameters": {}}},
        ]
        await selector.index_tools(tools)
        results = await selector.select_tools("read file contents", tools)
        assert len(results) <= 2
        result_names = [r["function"]["name"] for r in results]
        assert "read_file" in result_names

    @pytest.mark.asyncio
    async def test_select_tools_fallback_no_embeddings(self):
        selector = ToolSelector(embedding_service=None, top_k=2)
        tools = [
            {"function": {"name": "a", "description": "Alpha", "parameters": {}}},
            {"function": {"name": "b", "description": "Beta", "parameters": {}}},
            {"function": {"name": "c", "description": "Gamma", "parameters": {}}},
        ]
        results = await selector.select_tools("anything", tools)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_select_tools_empty_index_fallback(self):
        selector = ToolSelector(embedding_service=AsyncMock(), top_k=3)
        tools = [
            {"function": {"name": "a", "description": "A", "parameters": {}}},
        ]
        results = await selector.select_tools("query", tools)
        assert len(results) <= 3

    @pytest.mark.asyncio
    async def test_select_with_context(self):
        mock_embedder = AsyncMock()

        async def embed_fn(text):
            return [0.0, 0.0, 1.0]

        mock_embedder.embed = AsyncMock(side_effect=embed_fn)
        selector = ToolSelector(embedding_service=mock_embedder, top_k=5, min_similarity=0.0)
        tools = [
            {"function": {"name": "search_memory", "description": "Search long-term memory", "parameters": {}}},
        ]
        await selector.index_tools(tools)
        results = await selector.select_tools("find something", tools, context="Use memory tools")
        assert len(results) >= 1


class TestToolSelectorCosineSimilarity:
    def test_identical_vectors(self):
        selector = ToolSelector()
        sim = selector._cosine_similarity([1.0, 0.0, 0.0], [1.0, 0.0, 0.0])
        assert abs(sim - 1.0) < 1e-6

    def test_orthogonal_vectors(self):
        selector = ToolSelector()
        sim = selector._cosine_similarity([1.0, 0.0], [0.0, 1.0])
        assert abs(sim) < 1e-6

    def test_zero_vector(self):
        selector = ToolSelector()
        sim = selector._cosine_similarity([0.0, 0.0], [1.0, 0.0])
        assert sim == 0.0
