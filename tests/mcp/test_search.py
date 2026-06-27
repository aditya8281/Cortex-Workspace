"""Tests for MCP tool search — P04 Task 5."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.app.mcp.search import MCPToolSearch


class TestMCPToolSearchInit:
    def test_init_defaults(self):
        search = MCPToolSearch()
        assert search.top_k == 10
        assert search._indexed is False
        assert search._tool_index == {}

    def test_init_custom_top_k(self):
        search = MCPToolSearch(top_k=5)
        assert search.top_k == 5


class TestMCPToolSearchIndexing:
    @pytest.mark.asyncio
    async def test_index_tools(self):
        search = MCPToolSearch()
        tools = [
            {"function": {"name": "read_file", "description": "Read a file from disk", "parameters": {}}},
            {"function": {"name": "write_file", "description": "Write content to a file", "parameters": {}}},
        ]
        await search.index_tools(tools)
        assert search._indexed is True
        assert "read_file" in search._tool_index
        assert "write_file" in search._tool_index
        assert search._tool_index["read_file"]["description"] == "Read a file from disk"

    @pytest.mark.asyncio
    async def test_index_with_embeddings(self):
        mock_embedder = AsyncMock()
        mock_embedder.embed.return_value = [0.1, 0.2, 0.3]
        search = MCPToolSearch(embedding_service=mock_embedder)
        tools = [{"function": {"name": "tool1", "description": "A tool", "parameters": {}}}]
        await search.index_tools(tools)
        assert search._tool_index["tool1"]["embedding"] == [0.1, 0.2, 0.3]

    @pytest.mark.asyncio
    async def test_index_without_embeddings(self):
        search = MCPToolSearch()
        tools = [{"function": {"name": "tool1", "description": "A tool", "parameters": {}}}]
        await search.index_tools(tools)
        assert search._tool_index["tool1"]["embedding"] is None


class TestMCPToolSearchKeyword:
    @pytest.mark.asyncio
    async def test_keyword_search_finds_relevant(self):
        search = MCPToolSearch(top_k=3)
        tools = [
            {"function": {"name": "read_file", "description": "Read a file from disk", "parameters": {}}},
            {"function": {"name": "write_file", "description": "Write content to a file", "parameters": {}}},
            {"function": {"name": "search_memory", "description": "Search long-term memory", "parameters": {}}},
        ]
        await search.index_tools(tools)
        results = await search.search("file contents")
        assert len(results) <= 3
        # read_file and write_file should rank higher than search_memory
        result_names = [r["function"]["name"] for r in results]
        assert "search_memory" not in result_names[:2]

    @pytest.mark.asyncio
    async def test_keyword_search_top_k_limit(self):
        search = MCPToolSearch(top_k=2)
        tools = [
            {"function": {"name": "a", "description": "alpha", "parameters": {}}},
            {"function": {"name": "b", "description": "alpha beta", "parameters": {}}},
            {"function": {"name": "c", "description": "alpha beta gamma", "parameters": {}}},
        ]
        await search.index_tools(tools)
        results = await search.search("alpha beta gamma")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_keyword_search_empty_index(self):
        search = MCPToolSearch(top_k=5)
        results = await search.search("anything")
        assert results == []


class TestMCPToolSearchEmbedding:
    @pytest.mark.asyncio
    async def test_embedding_search_returns_top_k(self):
        mock_embedder = AsyncMock()
        # Query embedding, then tool embeddings for similarity
        mock_embedder.embed.side_effect = [
            [1.0, 0.0, 0.0],  # query
            [1.0, 0.0, 0.0],  # tool1 (high similarity)
            [0.0, 1.0, 0.0],  # tool2 (low similarity)
        ]
        search = MCPToolSearch(embedding_service=mock_embedder, top_k=1)
        tools = [
            {"function": {"name": "tool1", "description": "Alpha", "parameters": {}}},
            {"function": {"name": "tool2", "description": "Beta", "parameters": {}}},
        ]
        await search.index_tools(tools)
        results = await search.search("alpha")
        assert len(results) == 1
        assert results[0]["function"]["name"] == "tool1"


class TestMCPToolSearchEdgeCases:
    @pytest.mark.asyncio
    async def test_unindexed_returns_all(self):
        search = MCPToolSearch(top_k=2)
        search._tool_index = {
            "a": {"description": "A", "embedding": None, "schema": {"function": {"name": "a"}}},
            "b": {"description": "B", "embedding": None, "schema": {"function": {"name": "b"}}},
        }
        results = await search.search("anything")
        assert len(results) == 2

    def test_cosine_similarity_identical(self):
        search = MCPToolSearch()
        sim = search._cosine_similarity([1.0, 0.0], [1.0, 0.0])
        assert abs(sim - 1.0) < 1e-9

    def test_cosine_similarity_orthogonal(self):
        search = MCPToolSearch()
        sim = search._cosine_similarity([1.0, 0.0], [0.0, 1.0])
        assert abs(sim) < 1e-9

    def test_cosine_similarity_zero_vector(self):
        search = MCPToolSearch()
        sim = search._cosine_similarity([0.0, 0.0], [1.0, 0.0])
        assert sim == 0.0
