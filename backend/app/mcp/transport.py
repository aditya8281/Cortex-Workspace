"""MCP transport layers.

Two transport types:
1. stdio — for local servers (subprocess communication)
2. SSE — for remote servers (HTTP Server-Sent Events)

Both implement the same interface: send_request() and receive_events().
"""

from __future__ import annotations

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any

logger = logging.getLogger(__name__)


class MCPTransport(ABC):
    """Abstract MCP transport interface."""

    @abstractmethod
    async def send_request(self, request: dict) -> dict:
        """Send a JSON-RPC request and wait for the response."""
        pass

    @abstractmethod
    async def receive_events(self) -> AsyncGenerator[dict, None]:
        """Receive server-initiated events."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the transport connection."""
        pass


class StdioTransport(MCPTransport):
    """stdio transport for local MCP servers.

    Communicates via stdin/stdout of a subprocess.
    Each request is a JSON line. Each response is a JSON line.
    """

    def __init__(self, process: asyncio.subprocess.Process):
        self.process = process
        self._request_id = 0
        self._pending: dict[int, asyncio.Future] = {}
        self._read_task: asyncio.Task | None = None

    async def start(self):
        """Start reading responses in background."""
        self._read_task = asyncio.create_task(self._read_loop())

    async def _read_loop(self):
        """Continuously read responses from stdout."""
        try:
            while True:
                line = await self.process.stdout.readline()
                if not line:
                    break
                try:
                    response = json.loads(line.decode())
                    req_id = response.get("id")
                    if req_id and req_id in self._pending:
                        self._pending[req_id].set_result(response)
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON from MCP server: %s", line[:100])
        except asyncio.CancelledError:
            pass

    async def send_request(self, request: dict) -> dict:
        """Send request via stdin, wait for response."""
        self._request_id += 1
        request["id"] = self._request_id

        future = asyncio.get_event_loop().create_future()
        self._pending[self._request_id] = future

        data = json.dumps(request) + "\n"
        assert self.process.stdin is not None
        self.process.stdin.write(data.encode())
        await self.process.stdin.drain()

        try:
            response = await asyncio.wait_for(future, timeout=30)
            return response
        except asyncio.TimeoutError:
            self._pending.pop(self._request_id, None)
            raise RuntimeError(f"MCP request timed out: {request.get('method')}")

    async def receive_events(self) -> AsyncGenerator[dict, None]:  # type: ignore[override]
        """Receive server-initiated notifications."""
        while True:
            assert self.process.stdout is not None
            line = await self.process.stdout.readline()
            if not line:
                break
            try:
                msg = json.loads(line.decode())
                if "method" in msg and "id" not in msg:
                    yield msg
            except json.JSONDecodeError:
                pass

    async def close(self):
        """Close transport."""
        if self._read_task:
            self._read_task.cancel()
        for future in self._pending.values():
            if not future.done():
                future.cancel()
        self._pending.clear()


class SSETransport(MCPTransport):
    """SSE transport for remote MCP servers.

    Uses HTTP POST for requests and SSE for responses.
    """

    def __init__(self, sse_url: str):
        self.sse_url = sse_url
        self._session: Any = None
        self._request_id = 0

    async def connect(self):
        """Establish SSE connection."""
        import aiohttp

        self._session = aiohttp.ClientSession()

    async def send_request(self, request: dict) -> dict:
        """Send request via HTTP POST."""
        if not self._session:
            await self.connect()

        self._request_id += 1
        request["id"] = self._request_id

        async with self._session.post(
            self.sse_url,
            json=request,
            headers={"Content-Type": "application/json"},
        ) as resp:
            if resp.status != 200:
                raise RuntimeError(f"MCP SSE request failed: {resp.status}")
            return await resp.json()

    async def receive_events(self) -> AsyncGenerator[dict, None]:  # type: ignore[override]
        """Receive SSE events from server."""
        if not self._session:
            await self.connect()

        async with self._session.get(self.sse_url) as resp:
            async for line in resp.content:
                decoded = line.decode().strip()
                if decoded.startswith("data: "):
                    data = decoded[6:]
                    try:
                        yield json.loads(data)
                    except json.JSONDecodeError:
                        pass

    async def close(self):
        """Close SSE connection."""
        if self._session:
            await self._session.close()
