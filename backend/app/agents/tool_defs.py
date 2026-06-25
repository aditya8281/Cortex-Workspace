"""Agent tool implementations with approval flags.

Legacy TOOL_REGISTRY + new @tool decorator system.
Both systems are maintained during V1 Phase-2 transition.
"""

from __future__ import annotations

import asyncio
import ipaddress
import logging
import os
import shlex
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from backend.app.agents.tools.registry import tool
from backend.app.agents.tools.security import BLOCKED_URL_SCHEMES, has_blocked_command

logger = logging.getLogger(__name__)

AGENT_WORKSPACE = os.environ.get(
    "AGENT_WORKSPACE",
    os.path.join(os.path.expanduser("~"), ".cortex-agent-workspace"),
)

BLOCKED_HOSTS = frozenset(
    {
        "localhost",
        "127.0.0.1",
        "::1",
        "0.0.0.0",
        "169.254.169.254",
        "metadata.google.internal",
        "metadata.google.internal.",
    }
)


def _ensure_within_workspace(file_path: str) -> Path:
    """Resolve and validate that a file path is within the agent workspace."""
    workspace = Path(AGENT_WORKSPACE).resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    target = (workspace / file_path).resolve()
    if not str(target).startswith(str(workspace)):
        raise ValueError(f"Path traversal denied: {file_path}")
    return target


def _is_private_url(url: str) -> bool:
    """Check if URL targets a private/internal network."""
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            return False
        if hostname in BLOCKED_HOSTS:
            return True
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return True
        except ValueError:
            if hostname.endswith(".internal") or hostname.endswith(".local") or hostname.endswith(".localhost"):
                return True
        return False
    except Exception:
        return False


class UserInputRequired(Exception):
    """Raised when the agent needs user input to proceed."""

    def __init__(self, prompt: str):
        self.prompt = prompt
        super().__init__(prompt)


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


@tool(description="Run a shell command with safety limits", requires_approval=True, category="system")
async def exec_command(command: str) -> str:
    """Execute a shell command safely with safety limits and timeout.

    Args:
        command: The shell command to execute
    """
    command = command.strip()
    if not command:
        raise ValueError("Command is required")

    blocked = has_blocked_command(command)
    if blocked:
        raise ValueError(f"Blocked dangerous command pattern: {blocked}")

    try:
        parts = shlex.split(command)
    except ValueError:
        parts = command.split()

    workspace = Path(AGENT_WORKSPACE).resolve()
    workspace.mkdir(parents=True, exist_ok=True)

    proc = await asyncio.create_subprocess_exec(
        *parts,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(workspace),
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
    except asyncio.TimeoutError:
        proc.kill()
        return "Command timed out after 30 seconds"

    output = (stdout or b"").decode("utf-8", errors="replace")[:10240]
    err = (stderr or b"").decode("utf-8", errors="replace")[:2048]

    if proc.returncode != 0:
        return f"Exit {proc.returncode}\n{err}\n{output}".strip()
    return output or "(no output)"


@tool(description="Show recent git commits", category="code")
async def git_log(count: int = 10) -> str:
    """Show recent git commits.

    Args:
        count: Number of recent commits to show
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            "git",
            "log",
            "--oneline",
            f"-{count}",
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


@tool(description="Show file changes (git diff)", category="code")
async def git_diff(file_path: str | None = None) -> str:
    """Show file changes (git diff).

    Args:
        file_path: Optional specific file to diff
    """
    try:
        if file_path and file_path.startswith("-"):
            return "Error: invalid file path"
        args = ["git", "diff"]
        if file_path:
            args.append(file_path)
        proc = await asyncio.create_subprocess_exec(
            *args,
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


@tool(description="Fetch URL content (max 100KB)", requires_approval=True, category="web")
async def web_fetch(url: str) -> str | dict[str, str]:
    """Fetch URL content (max 100KB).

    Args:
        url: The URL to fetch
    """
    if any(url.lower().startswith(s) for s in BLOCKED_URL_SCHEMES):
        return {"error": f"URL scheme not allowed: {url}"}

    if _is_private_url(url):
        return {"error": "SSRF protection: URL targets a private/internal network and is blocked"}

    try:
        import urllib.request

        req = urllib.request.Request(url, headers={"User-Agent": "Cortex-Agent/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read(100 * 1024)
            return data.decode("utf-8", errors="replace")
    except Exception as e:
        return f"Error fetching URL: {e}"


@tool(description="Ask user for input — raises a signal for the run manager to handle", category="system")
async def ask_user(question: str) -> str:
    """Ask user for input. Raises UserInputRequired for run manager to handle.

    Args:
        question: The question to ask the user
    """
    raise UserInputRequired(question)


# Legacy registrations (backward compat)
register_tool("exec_command", exec_command, "Run a shell command with safety limits")
register_tool("git_log", git_log, "Show recent git commits")
register_tool("git_diff", git_diff, "Show file changes")
register_tool("web_fetch", web_fetch, "Fetch URL content")
register_tool("ask_user", ask_user, "Ask user for input")
