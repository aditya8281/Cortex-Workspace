"""Agent tool implementations with approval flags."""

from __future__ import annotations

import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

TOOL_REGISTRY: dict[str, dict[str, Any]] = {}

_REQUIRES_APPROVAL = {"exec_command", "write_file", "web_fetch"}


def requires_approval(tool_name: str) -> bool:
    return tool_name in _REQUIRES_APPROVAL


def register_tool(name: str, handler: Any, description: str = "") -> None:
    TOOL_REGISTRY[name] = {"handler": handler, "description": description}


def get_tool(name: str) -> Any | None:
    entry = TOOL_REGISTRY.get(name)
    return entry["handler"] if entry else None


def list_tools() -> dict[str, str]:
    return {name: entry["description"] for name, entry in TOOL_REGISTRY.items()}


async def exec_command(command: str, cwd: str = ".") -> str:
    """Run a shell command with safety limits (30s timeout, no rm -rf)."""
    forbidden = ["rm -rf", "rm -r /", "mkfs", ":(){", "fork bomb", "dd if=/dev"]
    cmd_lower = command.lower()
    for pattern in forbidden:
        if pattern in cmd_lower:
            return f"Blocked: command contains forbidden pattern '{pattern}'"

    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        output = stdout.decode("utf-8", errors="replace")
        err_output = stderr.decode("utf-8", errors="replace")
        if proc.returncode != 0:
            return f"Exit code {proc.returncode}\n{err_output}\n{output}"
        return output if output else err_output
    except asyncio.TimeoutError:
        return "Error: command timed out after 30 seconds"
    except Exception as e:
        return f"Error executing command: {e}"


async def git_log(repo_path: str = ".", count: int = 10) -> str:
    """Show recent git commits."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "git", "log", f"--oneline", f"-{count}",
            cwd=repo_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
        output = stdout.decode("utf-8", errors="replace")
        if proc.returncode != 0:
            return f"git error: {stderr.decode('utf-8', errors='replace')}"
        return output.strip() or "No commits found"
    except asyncio.TimeoutError:
        return "Error: git log timed out"
    except FileNotFoundError:
        return "Error: git not available"


async def git_diff(repo_path: str = ".", file_path: str | None = None) -> str:
    """Show file changes (git diff)."""
    try:
        args = ["git", "diff"]
        if file_path:
            args.append(file_path)
        proc = await asyncio.create_subprocess_exec(
            *args,
            cwd=repo_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
        output = stdout.decode("utf-8", errors="replace")
        if proc.returncode != 0:
            return f"git error: {stderr.decode('utf-8', errors='replace')}"
        return output.strip() or "No changes"
    except asyncio.TimeoutError:
        return "Error: git diff timed out"
    except FileNotFoundError:
        return "Error: git not available"


async def web_fetch(url: str) -> str:
    """Fetch URL content (max 100KB)."""
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={"User-Agent": "Cortex-Agent/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read(100 * 1024)
            return data.decode("utf-8", errors="replace")
    except Exception as e:
        return f"Error fetching URL: {e}"


async def ask_user(question: str) -> str:
    """Ask user for input. Returns placeholder — real implementation needs UI integration."""
    return f"[PENDING USER INPUT] {question}"


register_tool("exec_command", exec_command, "Run a shell command with safety limits")
register_tool("git_log", git_log, "Show recent git commits")
register_tool("git_diff", git_diff, "Show file changes")
register_tool("web_fetch", web_fetch, "Fetch URL content")
register_tool("ask_user", ask_user, "Ask user for input")
