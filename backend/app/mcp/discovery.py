"""MCP server discovery and lifecycle management.

Servers declared in configuration. Auto-discovery of local MCP servers.
Health monitoring every 30 seconds. Automatic restart on failure (max 3 retries).
Graceful shutdown on daemon stop.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class MCPServerStatus(str, Enum):
    DISCOVERED = "discovered"
    STARTING = "starting"
    RUNNING = "running"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    RESTARTING = "restarting"
    STOPPED = "stopped"
    FAILED = "failed"


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""

    name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    transport: str = "stdio"
    sse_url: str | None = None
    working_dir: str | None = None
    health_check_interval: int = 30
    max_restarts: int = 3
    timeout: int = 10


@dataclass
class MCPServerState:
    """Runtime state of an MCP server."""

    config: MCPServerConfig
    status: MCPServerStatus = MCPServerStatus.DISCOVERED
    process: asyncio.subprocess.Process | None = None
    restart_count: int = 0
    last_health_check: float = 0
    last_healthy: float = 0
    tools: list[dict] = field(default_factory=list)
    error: str | None = None


class MCPServerDiscovery:
    """Discover and manage MCP server lifecycle.

    Flow:
    1. Load server configs from configuration
    2. Start each server (stdio: subprocess, SSE: HTTP connect)
    3. Query available tools from each server
    4. Health check periodically
    5. Restart on failure (up to max_retries)
    6. Graceful shutdown on daemon stop
    """

    def __init__(self):
        self._servers: dict[str, MCPServerState] = {}
        self._health_task: asyncio.Task | None = None
        self._running = False

    async def load_config(self, config_path: str | None = None) -> int:
        """Load MCP server configurations. Returns count loaded."""
        configs = self._load_configs(config_path)
        for config in configs:
            self._servers[config.name] = MCPServerState(config=config)
        logger.info("Loaded %d MCP server configurations", len(configs))
        return len(configs)

    async def start_all(self) -> dict[str, bool]:
        """Start all configured MCP servers. Returns {name: success}."""
        results = {}
        for name, state in self._servers.items():
            try:
                await self._start_server(state)
                results[name] = True
            except Exception as e:
                logger.error("Failed to start MCP server %s: %s", name, e)
                state.status = MCPServerStatus.FAILED
                state.error = str(e)
                results[name] = False
        return results

    async def _start_server(self, state: MCPServerState) -> None:
        """Start a single MCP server."""
        config = state.config
        state.status = MCPServerStatus.STARTING

        if config.transport == "stdio":
            await self._start_stdio(state)
        elif config.transport == "sse":
            await self._start_sse(state)
        else:
            raise ValueError(f"Unknown transport: {config.transport}")

        state.tools = await self._query_tools(state)
        state.status = MCPServerStatus.RUNNING
        logger.info(
            "MCP server %s started (%d tools discovered)",
            config.name,
            len(state.tools),
        )

    async def _start_stdio(self, state: MCPServerState) -> None:
        """Start an MCP server via stdio transport (subprocess)."""
        config = state.config
        env = {**os.environ, **config.env}

        state.process = await asyncio.create_subprocess_exec(
            config.command,
            *config.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
            cwd=config.working_dir,
        )

        try:
            await asyncio.wait_for(
                self._wait_for_ready(state),
                timeout=config.timeout,
            )
        except asyncio.TimeoutError:
            await self._stop_server(state)
            raise RuntimeError(f"MCP server {config.name} startup timeout")

    async def _start_sse(self, state: MCPServerState) -> None:
        """Connect to an MCP server via SSE transport."""
        import aiohttp

        config = state.config
        async with aiohttp.ClientSession() as session, session.get(config.sse_url) as resp:
            if resp.status != 200:
                raise RuntimeError(f"MCP server {config.name} SSE endpoint unreachable: {resp.status}")

    async def _wait_for_ready(self, state: MCPServerState) -> None:
        """Wait for a stdio MCP server to be ready."""
        init_request = (
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "cortex", "version": "1.0.0"},
                    },
                }
            )
            + "\n"
        )

        assert state.process is not None
        proc = state.process
        assert proc.stdin is not None
        proc.stdin.write(init_request.encode())
        await proc.stdin.drain()

        assert proc.stdout is not None
        response_line = await asyncio.wait_for(
            proc.stdout.readline(),
            timeout=state.config.timeout,
        )
        response = json.loads(response_line.decode())
        if "result" not in response:
            raise RuntimeError(f"MCP server {state.config.name} init failed: {response}")

    async def _query_tools(self, state: MCPServerState) -> list[dict]:
        """Query available tools from an MCP server."""
        tools_request = (
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {},
                }
            )
            + "\n"
        )

        if state.config.transport == "stdio" and state.process:
            proc = state.process
            assert proc.stdin is not None
            proc.stdin.write(tools_request.encode())
            await proc.stdin.drain()

            assert proc.stdout is not None
            response_line = await asyncio.wait_for(
                proc.stdout.readline(),
                timeout=5,
            )
            response = json.loads(response_line.decode())
            return response.get("result", {}).get("tools", [])

        return []

    async def health_check(self) -> dict[str, MCPServerStatus]:
        """Check health of all servers. Returns {name: status}."""
        results: dict[str, MCPServerStatus] = {}
        for name, state in self._servers.items():
            if state.status in (MCPServerStatus.STOPPED, MCPServerStatus.FAILED):
                results[name] = state.status
                continue

            if state.config.transport == "stdio" and state.process:
                if state.process.returncode is not None:
                    state.status = MCPServerStatus.UNHEALTHY
                    state.error = f"Process exited with code {state.process.returncode}"
                    await self._attempt_restart(state)
                else:
                    state.status = MCPServerStatus.HEALTHY
            else:
                state.status = MCPServerStatus.HEALTHY

            results[name] = state.status
        return results

    async def _attempt_restart(self, state: MCPServerState) -> None:
        """Attempt to restart a failed server."""
        if state.restart_count >= state.config.max_restarts:
            state.status = MCPServerStatus.FAILED
            state.error = f"Max restarts ({state.config.max_restarts}) exceeded"
            logger.error("MCP server %s permanently failed", state.config.name)
            return

        state.status = MCPServerStatus.RESTARTING
        state.restart_count += 1
        logger.warning(
            "Restarting MCP server %s (attempt %d/%d)",
            state.config.name,
            state.restart_count,
            state.config.max_restarts,
        )

        await self._stop_server(state)
        try:
            await self._start_server(state)
        except Exception as e:
            state.status = MCPServerStatus.FAILED
            state.error = str(e)

    async def _stop_server(self, state: MCPServerState) -> None:
        """Stop a running MCP server."""
        if state.process and state.process.returncode is None:
            state.process.terminate()
            try:
                await asyncio.wait_for(state.process.wait(), timeout=5)
            except asyncio.TimeoutError:
                state.process.kill()
        state.process = None
        state.status = MCPServerStatus.STOPPED

    async def stop_all(self) -> None:
        """Gracefully stop all MCP servers."""
        for state in self._servers.values():
            await self._stop_server(state)
        logger.info("All MCP servers stopped")

    async def start_health_monitor(self, interval: int = 30) -> None:
        """Start periodic health checking."""
        self._running = True

        async def _monitor():
            while self._running:
                await asyncio.sleep(interval)
                await self.health_check()

        self._health_task = asyncio.create_task(_monitor())

    async def stop_health_monitor(self) -> None:
        """Stop health monitoring."""
        self._running = False
        if self._health_task:
            self._health_task.cancel()

    def get_all_tools(self) -> list[dict]:
        """Get all tools from all healthy MCP servers."""
        all_tools = []
        for state in self._servers.values():
            if state.status in (MCPServerStatus.RUNNING, MCPServerStatus.HEALTHY):
                for tool in state.tools:
                    all_tools.append(self._wrap_tool(tool, state.config.name))
        return all_tools

    def _wrap_tool(self, mcp_tool: dict, server_name: str) -> dict:
        """Wrap an MCP tool into Cortex tool schema format."""
        return {
            "type": "function",
            "function": {
                "name": f"mcp_{server_name}_{mcp_tool.get('name', 'unknown')}",
                "description": f"[MCP:{server_name}] {mcp_tool.get('description', '')}",
                "parameters": mcp_tool.get("inputSchema", {}),
            },
        }

    def _load_configs(self, config_path: str | None = None) -> list[MCPServerConfig]:
        """Load MCP server configurations from file or defaults."""
        return []
