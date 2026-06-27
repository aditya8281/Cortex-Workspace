"""Tests for MCP transport layers — P04 Task 3."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.mcp.transport import MCPTransport, SSETransport, StdioTransport


class TestMCPTransportABC:
    def test_cannot_instantiate_abstract(self):
        with pytest.raises(TypeError):
            MCPTransport()


class TestStdioTransport:
    def test_init(self):
        proc = MagicMock()
        transport = StdioTransport(proc)
        assert transport.process is proc
        assert transport._request_id == 0
        assert transport._pending == {}

    @pytest.mark.asyncio
    async def test_send_request_increments_id(self):
        proc = MagicMock()
        proc.stdin = MagicMock()
        proc.stdin.write = MagicMock()
        proc.stdin.drain = AsyncMock()
        proc.stdout = AsyncMock()

        transport = StdioTransport(proc)
        transport._request_id = 5

        fake_response = {"jsonrpc": "2.0", "id": 6, "result": {}}
        with patch("asyncio.wait_for", new_callable=AsyncMock, return_value=fake_response):
            request = {"jsonrpc": "2.0", "method": "tools/list", "params": {}}
            result = await transport.send_request(request)

        assert result["id"] == 6
        assert transport._request_id == 6

    @pytest.mark.asyncio
    async def test_send_request_writes_to_stdin(self):
        proc = MagicMock()
        proc.stdin = MagicMock()
        proc.stdin.write = MagicMock()
        proc.stdin.drain = AsyncMock()
        proc.stdout = AsyncMock()

        transport = StdioTransport(proc)

        fake_response = {"jsonrpc": "2.0", "id": 1, "result": {}}
        with patch("asyncio.wait_for", new_callable=AsyncMock, return_value=fake_response):
            await transport.send_request({"jsonrpc": "2.0", "method": "test", "params": {}})
        proc.stdin.write.assert_called_once()
        proc.stdin.drain.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_request_timeout(self):
        proc = MagicMock()
        proc.stdin = MagicMock()
        proc.stdin.write = MagicMock()
        proc.stdin.drain = AsyncMock()
        proc.stdout = AsyncMock()

        transport = StdioTransport(proc)

        loop = asyncio.get_event_loop()
        future = loop.create_future()
        transport._pending[1] = future

        with (
            patch("asyncio.wait_for", side_effect=asyncio.TimeoutError),
            pytest.raises(RuntimeError, match="timed out"),
        ):
            await transport.send_request({"jsonrpc": "2.0", "id": 1, "method": "test", "params": {}})

    @pytest.mark.asyncio
    async def test_close_clears_pending(self):
        proc = MagicMock()
        transport = StdioTransport(proc)
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        transport._pending[1] = future
        transport._read_task = MagicMock()
        transport._read_task.cancel = MagicMock()

        await transport.close()
        transport._read_task.cancel.assert_called_once()
        assert transport._pending == {}


class TestSSETransport:
    def test_init(self):
        transport = SSETransport("https://example.com/sse")
        assert transport.sse_url == "https://example.com/sse"
        assert transport._session is None
        assert transport._request_id == 0

    @pytest.mark.asyncio
    async def test_send_request_success(self):
        transport = SSETransport("https://example.com/sse")
        mock_session = AsyncMock()
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"jsonrpc": "2.0", "id": 1, "result": {}})
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_session.post = MagicMock(return_value=mock_ctx)

        transport._session = mock_session
        result = await transport.send_request({"jsonrpc": "2.0", "method": "test", "params": {}})
        assert result["id"] == 1
        assert transport._request_id == 1

    @pytest.mark.asyncio
    async def test_send_request_raises_on_failure(self):
        transport = SSETransport("https://example.com/sse")
        mock_session = AsyncMock()
        mock_resp = AsyncMock()
        mock_resp.status = 500
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_session.post = MagicMock(return_value=mock_ctx)

        transport._session = mock_session
        with pytest.raises(RuntimeError, match="failed"):
            await transport.send_request({"jsonrpc": "2.0", "method": "test", "params": {}})

    @pytest.mark.asyncio
    async def test_close(self):
        transport = SSETransport("https://example.com/sse")
        mock_session = AsyncMock()
        transport._session = mock_session
        await transport.close()
        mock_session.close.assert_called_once()
