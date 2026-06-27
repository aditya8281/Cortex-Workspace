"""Tests for tool execution sandbox — P05 Task 5."""

from __future__ import annotations

import asyncio

import pytest

from backend.app.agents.tools.sandbox import (
    TOOL_SANDBOX_CONFIGS,
    SandboxConfig,
    SandboxResult,
    ToolSandbox,
)


class TestSandboxConfig:
    def test_default_values(self):
        config = SandboxConfig()
        assert config.timeout_seconds == 30
        assert config.max_output_bytes == 100_000
        assert config.max_retries == 0

    def test_custom_values(self):
        config = SandboxConfig(timeout_seconds=10, max_output_bytes=50_000)
        assert config.timeout_seconds == 10
        assert config.max_output_bytes == 50_000


class TestSandboxResult:
    def test_success_result(self):
        result = SandboxResult(success=True, result="ok", duration_ms=10.5)
        assert result.success is True
        assert result.result == "ok"
        assert result.error is None
        assert result.timed_out is False
        assert result.output_truncated is False

    def test_failure_result(self):
        result = SandboxResult(success=False, error="timeout", timed_out=True)
        assert result.success is False
        assert result.error == "timeout"
        assert result.timed_out is True


class TestToolSandboxExecute:
    @pytest.mark.asyncio
    async def test_successful_execution(self):
        sandbox = ToolSandbox()

        async def my_tool(x: int = 5) -> str:
            return f"result: {x}"

        result = await sandbox.execute("test_tool", my_tool, {"x": 42})
        assert result.success is True
        assert result.result == "result: 42"
        assert result.duration_ms > 0

    @pytest.mark.asyncio
    async def test_timeout_enforced(self):
        sandbox = ToolSandbox(default_config=SandboxConfig(timeout_seconds=1))

        async def slow_tool():
            await asyncio.sleep(10)
            return "done"

        result = await sandbox.execute("test_tool", slow_tool, {})
        assert result.success is False
        assert result.timed_out is True
        assert "timed out" in result.error

    @pytest.mark.asyncio
    async def test_output_truncation(self):
        sandbox = ToolSandbox(default_config=SandboxConfig(max_output_bytes=100))

        async def large_output():
            return "x" * 500

        result = await sandbox.execute("test_tool", large_output, {})
        assert result.success is True
        assert result.output_truncated is True
        assert "[...truncated...]" in result.result

    @pytest.mark.asyncio
    async def test_no_truncation_under_limit(self):
        sandbox = ToolSandbox(default_config=SandboxConfig(max_output_bytes=1000))

        async def small_output():
            return "hello"

        result = await sandbox.execute("test_tool", small_output, {})
        assert result.success is True
        assert result.output_truncated is False
        assert result.result == "hello"

    @pytest.mark.asyncio
    async def test_exception_caught(self):
        sandbox = ToolSandbox()

        async def failing_tool():
            raise ValueError("bad input")

        result = await sandbox.execute("test_tool", failing_tool, {})
        assert result.success is False
        assert "ValueError" in result.error
        assert "bad input" in result.error
        assert result.duration_ms > 0

    @pytest.mark.asyncio
    async def test_per_tool_config(self):
        assert "execute_command" in TOOL_SANDBOX_CONFIGS
        assert TOOL_SANDBOX_CONFIGS["execute_command"].timeout_seconds == 60

    @pytest.mark.asyncio
    async def test_sync_handler_via_sandbox(self):
        sandbox = ToolSandbox()

        def sync_tool(x: int = 1) -> int:
            return x * 2

        result = await sandbox.execute("test_tool", sync_tool, {"x": 5})
        assert result.success is True
        assert result.result == "10"


class TestToolSandboxStats:
    @pytest.mark.asyncio
    async def test_stats_tracking(self):
        sandbox = ToolSandbox()

        async def my_tool():
            return "ok"

        await sandbox.execute("tool_a", my_tool, {})
        await sandbox.execute("tool_a", my_tool, {})
        await sandbox.execute("tool_b", my_tool, {})

        stats = sandbox.get_stats()
        assert "tool_a" in stats
        assert "tool_b" in stats
        assert stats["tool_a"]["executions"] == 2
        assert stats["tool_b"]["executions"] == 1
        assert stats["tool_a"]["avg_ms"] > 0

    def test_stats_empty(self):
        sandbox = ToolSandbox()
        stats = sandbox.get_stats()
        assert stats == {}
