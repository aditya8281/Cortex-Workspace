"""Tool execution sandbox — P05 Task 5.

Enforces resource limits (timeout, output size) on tool execution.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SandboxConfig:
    """Configuration for tool execution limits."""

    timeout_seconds: int = 30
    max_output_bytes: int = 100_000
    max_retries: int = 0


@dataclass
class SandboxResult:
    """Result of a sandboxed tool execution."""

    success: bool
    result: Any = None
    error: str | None = None
    duration_ms: float = 0.0
    timed_out: bool = False
    output_truncated: bool = False


# Per-tool sandbox configs for tools that need special limits
TOOL_SANDBOX_CONFIGS: dict[str, SandboxConfig] = {
    "execute_command": SandboxConfig(timeout_seconds=60, max_output_bytes=200_000),
    "web_fetch": SandboxConfig(timeout_seconds=15),
    "read_file": SandboxConfig(timeout_seconds=10),
}


@dataclass
class ToolSandbox:
    """Executes tools with resource limits enforced."""

    default_config: SandboxConfig = field(default_factory=SandboxConfig)
    _stats: dict[str, dict[str, Any]] = field(default_factory=dict)

    async def execute(
        self,
        tool_name: str,
        handler: Callable[..., Any],
        args: dict[str, Any],
    ) -> SandboxResult:
        """Execute a tool handler with sandbox limits."""
        config = TOOL_SANDBOX_CONFIGS.get(tool_name, self.default_config)
        start = time.monotonic()

        try:
            # Wrap handler call with timeout
            result = await asyncio.wait_for(
                self._call_handler(handler, args),
                timeout=config.timeout_seconds,
            )

            duration_ms = (time.monotonic() - start) * 1000

            # Convert result to string and check truncation
            result_str = str(result)
            truncated = False
            if len(result_str.encode("utf-8")) > config.max_output_bytes:
                # Truncate to max_output_bytes
                encoded = result_str.encode("utf-8")[: config.max_output_bytes]
                result_str = encoded.decode("utf-8", errors="ignore")
                result_str += "\n[...truncated...]"
                truncated = True

            self._record_stat(tool_name, duration_ms, True)

            return SandboxResult(
                success=True,
                result=result_str,
                duration_ms=duration_ms,
                output_truncated=truncated,
            )

        except asyncio.TimeoutError:
            duration_ms = (time.monotonic() - start) * 1000
            self._record_stat(tool_name, duration_ms, False)
            return SandboxResult(
                success=False,
                error=f"Tool '{tool_name}' timed out after {config.timeout_seconds}s",
                duration_ms=duration_ms,
                timed_out=True,
            )
        except Exception as e:
            duration_ms = (time.monotonic() - start) * 1000
            self._record_stat(tool_name, duration_ms, False)
            return SandboxResult(
                success=False,
                error=f"{type(e).__name__}: {e}",
                duration_ms=duration_ms,
            )

    async def _call_handler(self, handler: Callable[..., Any], args: dict[str, Any]) -> Any:
        """Call a handler, supporting both sync and async."""
        if asyncio.iscoroutinefunction(handler):
            return await handler(**args)
        else:
            # Run sync handler in thread executor to avoid blocking
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, lambda: handler(**args))

    def _record_stat(self, tool_name: str, duration_ms: float, success: bool) -> None:
        """Record execution stats for a tool."""
        if tool_name not in self._stats:
            self._stats[tool_name] = {
                "executions": 0,
                "successes": 0,
                "total_ms": 0.0,
            }
        stats = self._stats[tool_name]
        stats["executions"] += 1
        if success:
            stats["successes"] += 1
        stats["total_ms"] += duration_ms

    def get_stats(self) -> dict[str, dict[str, Any]]:
        """Return execution stats per tool."""
        result: dict[str, dict[str, Any]] = {}
        for tool_name, stats in self._stats.items():
            executions = stats["executions"]
            result[tool_name] = {
                "executions": executions,
                "successes": stats["successes"],
                "avg_ms": stats["total_ms"] / executions if executions > 0 else 0.0,
            }
        return result
