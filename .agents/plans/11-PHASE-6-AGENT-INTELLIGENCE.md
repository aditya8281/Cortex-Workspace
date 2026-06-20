# Phase 6: Agent Intelligence

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Multi-step agent reasoning with tool chaining, workflow execution, and real-time step streaming. Agents can plan, execute, observe, and adapt.

**Architecture:** Enhanced ExecutorAgent with LLM-driven tool calling, tool registry with new tools (shell, git, web fetch), SSE streaming for real-time step updates, and agent performance metrics.

**Tech Stack:** Python 3.12+, SQLAlchemy 2.0, SSE (Server-Sent Events), Next.js 15, httpx, asyncio.Queue

---

## Task 1: Expanded Tool Registry

**Files:**
- Create: `backend/app/agents/tools/__init__.py`
- Create: `backend/app/agents/tools/shell.py`
- Create: `backend/app/agents/tools/git_tools.py`
- Create: `backend/app/agents/tools/web_fetch.py`
- Modify: `backend/app/agents/executor.py` (register new tools)

- [ ] **Step 1: Create the tools package with a ToolProtocol and registry**

```python
# backend/app/agents/tools/__init__.py
"""
Tool registry — typed tool definitions with JSON Schema parameters.

Every tool module exposes:
  - name: str
  - description: str
  - parameters: dict  (JSON Schema for the tool's arguments)
  - execute: async callable(**kwargs) -> str
"""

from __future__ import annotations

import logging
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class Tool(Protocol):
    """Protocol that every tool must satisfy."""

    name: str
    description: str
    parameters: dict  # JSON Schema

    async def execute(self, **kwargs: Any) -> str: ...


class ToolRegistry:
    """Central registry of available tools.

    Usage:
        registry = ToolRegistry()
        registry.register(ShellExecTool())
        schemas = registry.get_schemas()
        result = await registry.execute("shell_exec", command="ls -la")
    """

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool instance."""
        if not isinstance(tool, Tool):
            raise TypeError(f"Object {tool!r} does not implement the Tool protocol")
        self._tools[tool.name] = tool
        logger.debug("Registered tool: %s", tool.name)

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[Tool]:
        return list(self._tools.values())

    def get_schemas(self) -> list[dict]:
        """Return OpenAI-compatible function-calling schemas for all tools."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            }
            for tool in self._tools.values()
        ]

    async def execute(self, name: str, **kwargs: Any) -> str:
        """Execute a tool by name."""
        tool = self._tools.get(name)
        if not tool:
            raise ValueError(f"Unknown tool: {name}")
        return await tool.execute(**kwargs)

    def __len__(self) -> int:
        return len(self._tools)

    def __repr__(self) -> str:
        names = ", ".join(self._tools.keys())
        return f"ToolRegistry({len(self._tools)} tools: {names})"
```

- [ ] **Step 2: Implement the shell_exec tool**

```python
# backend/app/agents/tools/shell.py
"""
Shell execution tool — runs arbitrary shell commands via subprocess.

NO SANDBOXING in this phase. Uses subprocess.run with a configurable timeout.
"""

from __future__ import annotations

import logging
import subprocess
from typing import Any

logger = logging.getLogger(__name__)

TOOL_NAME = "shell_exec"
TOOL_DESCRIPTION = (
    "Execute a shell command on the host system and return its combined stdout + stderr. "
    "Use for running build scripts, checking git status, listing directories, etc. "
    "Commands run in the current working directory with no sandbox."
)

PARAMETERS: dict = {
    "type": "object",
    "properties": {
        "command": {
            "type": "string",
            "description": "The shell command to execute (e.g. 'ls -la', 'git status')",
        },
        "timeout": {
            "type": "integer",
            "description": "Maximum seconds to wait before killing the process (default: 30)",
            "default": 30,
        },
        "cwd": {
            "type": "string",
            "description": "Working directory for the command (optional, defaults to current dir)",
        },
    },
    "required": ["command"],
}

DEFAULT_TIMEOUT = 30
MAX_OUTPUT_CHARS = 20_000


class ShellExecTool:
    """Execute shell commands via subprocess.run."""

    name = TOOL_NAME
    description = TOOL_DESCRIPTION
    parameters = PARAMETERS

    async def execute(
        self,
        command: str,
        timeout: int = DEFAULT_TIMEOUT,
        cwd: str | None = None,
        **kwargs: Any,
    ) -> str:
        logger.info("shell_exec: %s (cwd=%s, timeout=%ds)", command, cwd, timeout)
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd,
            )
            parts: list[str] = []
            if result.stdout:
                stdout = result.stdout[:MAX_OUTPUT_CHARS]
                if len(result.stdout) > MAX_OUTPUT_CHARS:
                    stdout += f"\n... (truncated, {len(result.stdout)} total chars)"
                parts.append(f"STDOUT:\n{stdout}")
            if result.stderr:
                stderr = result.stderr[:MAX_OUTPUT_CHARS]
                if len(result.stderr) > MAX_OUTPUT_CHARS:
                    stderr += f"\n... (truncated, {len(result.stderr)} total chars)"
                parts.append(f"STDERR:\n{stderr}")
            parts.append(f"EXIT CODE: {result.returncode}")
            return "\n".join(parts) if parts else "(no output)"
        except subprocess.TimeoutExpired:
            return f"ERROR: Command timed out after {timeout}s"
        except Exception as e:
            return f"ERROR: {e}"
```

- [ ] **Step 3: Implement git tools (git_log, git_diff)**

```python
# backend/app/agents/tools/git_tools.py
"""
Git tools — git_log and git_diff for inspecting repository history.
"""

from __future__ import annotations

import logging
import subprocess
from typing import Any

logger = logging.getLogger(__name__)

MAX_OUTPUT_CHARS = 15_000


def _run_git(args: list[str], cwd: str | None = None) -> str:
    """Run a git command and return combined output."""
    cmd = ["git"] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=15,
            cwd=cwd,
        )
        output = result.stdout.strip()
        if result.stderr.strip():
            output = f"{output}\nSTDERR: {result.stderr.strip()}" if output else result.stderr.strip()
        if not output:
            output = "(no output)"
        return output[:MAX_OUTPUT_CHARS]
    except FileNotFoundError:
        return "ERROR: git is not installed or not in PATH"
    except subprocess.TimeoutExpired:
        return "ERROR: git command timed out after 15s"
    except Exception as e:
        return f"ERROR: {e}"


# ── git_log ───────────────────────────────────────────────────────

GIT_LOG_NAME = "git_log"
GIT_LOG_DESCRIPTION = (
    "Show recent git commits in the repository. "
    "Returns commit hash, author, date, and message for each commit."
)
GIT_LOG_PARAMETERS: dict = {
    "type": "object",
    "properties": {
        "count": {
            "type": "integer",
            "description": "Number of recent commits to show (default: 10)",
            "default": 10,
        },
        "cwd": {
            "type": "string",
            "description": "Path to the git repository (optional)",
        },
    },
    "required": [],
}


class GitLogTool:
    """Show recent git commits."""

    name = GIT_LOG_NAME
    description = GIT_LOG_DESCRIPTION
    parameters = GIT_LOG_PARAMETERS

    async def execute(self, count: int = 10, cwd: str | None = None, **kwargs: Any) -> str:
        count = max(1, min(count, 50))
        logger.info("git_log: count=%d, cwd=%s", count, cwd)
        return _run_git(["log", f"--oneline", f"-{count}", "--decorate"], cwd=cwd)


# ── git_diff ──────────────────────────────────────────────────────

GIT_DIFF_NAME = "git_diff"
GIT_DIFF_DESCRIPTION = (
    "Show file changes in the working tree or between commits. "
    "Without arguments, shows unstaged changes. Optionally compare two refs."
)
GIT_DIFF_PARAMETERS: dict = {
    "type": "object",
    "properties": {
        "ref_a": {
            "type": "string",
            "description": "First git ref (commit, branch, tag) for comparison. If omitted, shows working tree diff.",
        },
        "ref_b": {
            "type": "string",
            "description": "Second git ref to compare against ref_a.",
        },
        "cwd": {
            "type": "string",
            "description": "Path to the git repository (optional)",
        },
    },
    "required": [],
}


class GitDiffTool:
    """Show git diffs."""

    name = GIT_DIFF_NAME
    description = GIT_DIFF_DESCRIPTION
    parameters = GIT_DIFF_PARAMETERS

    async def execute(
        self,
        ref_a: str | None = None,
        ref_b: str | None = None,
        cwd: str | None = None,
        **kwargs: Any,
    ) -> str:
        args: list[str] = ["diff"]
        if ref_a and ref_b:
            args = ["diff", ref_a, ref_b]
        elif ref_a:
            args = ["diff", ref_a]
        logger.info("git_diff: args=%s, cwd=%s", args, cwd)
        return _run_git(args, cwd=cwd)
```

- [ ] **Step 4: Implement the web_fetch tool**

```python
# backend/app/agents/tools/web_fetch.py
"""
Web fetch tool — simple HTTP GET wrapper using httpx.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

TOOL_NAME = "web_fetch"
TOOL_DESCRIPTION = (
    "Fetch the content of a URL via HTTP GET. "
    "Returns the response body (truncated to 20k chars). "
    "Useful for reading documentation, API responses, or raw file contents from the web."
)
PARAMETERS: dict = {
    "type": "object",
    "properties": {
        "url": {
            "type": "string",
            "description": "The URL to fetch (must be a valid HTTP/HTTPS URL)",
        },
        "max_chars": {
            "type": "integer",
            "description": "Maximum characters to return (default: 20000)",
            "default": 20000,
        },
    },
    "required": ["url"],
}

DEFAULT_MAX_CHARS = 20_000
REQUEST_TIMEOUT = 15


class WebFetchTool:
    """Fetch URL content via httpx."""

    name = TOOL_NAME
    description = TOOL_DESCRIPTION
    parameters = PARAMETERS

    async def execute(
        self,
        url: str,
        max_chars: int = DEFAULT_MAX_CHARS,
        **kwargs: Any,
    ) -> str:
        logger.info("web_fetch: %s", url)

        try:
            import httpx
        except ImportError:
            return "ERROR: httpx is not installed. Run: pip install httpx"

        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=REQUEST_TIMEOUT) as client:
                response = await client.get(
                    url,
                    headers={"User-Agent": "CortexAgent/1.0"},
                )
                response.raise_for_status()
                content = response.text[:max_chars]
                if len(response.text) > max_chars:
                    content += f"\n... (truncated, {len(response.text)} total chars)"
                return f"STATUS: {response.status_code}\nCONTENT_TYPE: {response.headers.get('content-type', 'unknown')}\n\n{content}"
        except httpx.TimeoutException:
            return f"ERROR: Request timed out after {REQUEST_TIMEOUT}s"
        except httpx.HTTPStatusError as e:
            return f"ERROR: HTTP {e.response.status_code} — {e.response.text[:500]}"
        except Exception as e:
            return f"ERROR: {e}"
```

- [ ] **Step 5: Register all new tools in ExecutorAgent**

```python
# backend/app/agents/executor.py — REPLACE entire file
"""Executor agent — completes tasks using available tools."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from backend.app.agents.base import BaseAgent
from backend.app.agents.tools import ToolRegistry
from backend.app.agents.tools.shell import ShellExecTool
from backend.app.agents.tools.git_tools import GitLogTool, GitDiffTool
from backend.app.agents.tools.web_fetch import WebFetchTool

logger = logging.getLogger(__name__)

EXECUTOR_SYSTEM_PROMPT = """You are an executor agent for a code intelligence system.
You complete tasks by using available tools: search, read_file, write_file, list_files,
shell_exec, git_log, git_diff, and web_fetch.

When given a task:
1. Think about what tools you need
2. Use the tools to gather information or make changes
3. Report your results

Always explain what you did and what you found."""


class ExecutorAgent(BaseAgent):
    """Executes tasks using available tools."""

    def __init__(self, search_fn: Any | None = None, llm_chat: Any | None = None):
        super().__init__(system_prompt=EXECUTOR_SYSTEM_PROMPT)
        self._search_fn = search_fn
        self._llm_chat = llm_chat

        # Central tool registry
        self.tool_registry = ToolRegistry()
        self._register_default_tools()

        # Keep backward-compat _tools dict synced with registry
        self._sync_tools_from_registry()

    def _register_default_tools(self) -> None:
        """Register all built-in tools into the registry."""
        self.tool_registry.register(ShellExecTool())
        self.tool_registry.register(GitLogTool())
        self.tool_registry.register(GitDiffTool())
        self.tool_registry.register(WebFetchTool())

        # Also register the original search/file tools as lambdas
        # (these don't need full Tool protocol, they're already in _tools)
        self.register_tool("search", self._search_tool)
        self.register_tool("read_file", self._read_file_tool)
        self.register_tool("write_file", self._write_file_tool)
        self.register_tool("list_files", self._list_files_tool)

    def _sync_tools_from_registry(self) -> None:
        """Copy registry tools into the legacy _tools dict for backward compat."""
        for tool in self.tool_registry.list_tools():
            if tool.name not in self._tools:
                self._tools[tool.name] = tool.execute

    def get_tool_schemas(self) -> list[dict]:
        """Return combined schemas from registry + legacy tools."""
        schemas = self.tool_registry.get_schemas()
        # Add legacy tools that aren't in the registry
        registry_names = {t.name for t in self.tool_registry.list_tools()}
        for name, handler in self._tools.items():
            if name not in registry_names:
                schemas.append({
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": getattr(handler, "__doc__", f"Tool: {name}"),
                    },
                })
        return schemas

    async def execute_tool(self, name: str, **kwargs: Any) -> Any:
        """Execute a tool — registry takes priority, then legacy _tools."""
        # Try registry first
        if self.tool_registry.get(name):
            return await self.tool_registry.execute(name, **kwargs)
        # Fall back to legacy
        handler = self._tools.get(name)
        if not handler:
            raise ValueError(f"Unknown tool: {name}")
        import inspect
        if inspect.iscoroutinefunction(handler):
            return await handler(**kwargs)
        return handler(**kwargs)

    def _default_prompt(self) -> str:
        return EXECUTOR_SYSTEM_PROMPT

    async def run(self, input_text: str, context: dict | None = None) -> str:
        """Execute a task and return the result."""
        if self._llm_chat:
            return await self._execute_with_llm(input_text, context)
        return await self._execute_direct(input_text, context)

    async def _execute_with_llm(self, task: str, context: dict | None = None) -> str:
        """Use LLM with tool calling to execute a task."""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": task},
        ]
        if context:
            messages.append({
                "role": "user",
                "content": f"Context from previous steps:\n{context}",
            })

        max_iterations = 10
        for _ in range(max_iterations):
            try:
                result = await self._llm_chat(messages, self.get_tool_schemas())
                text = result[0] if isinstance(result, tuple) else str(result)
                if isinstance(result, tuple) and len(result) > 1 and result[1]:
                    tool_calls = result[1]
                    for call in tool_calls:
                        tool_name = call.get("name", "")
                        tool_args = call.get("arguments", {})
                        observation = await self.execute_tool(tool_name, **tool_args)
                        messages.append({
                            "role": "assistant",
                            "content": text,
                            "tool_calls": [call],
                        })
                        messages.append({
                            "role": "tool",
                            "content": str(observation),
                        })
                else:
                    return text
            except Exception as e:
                logger.error("LLM execution failed: %s", e)
                return f"Execution failed: {e}"
        return "Task completed with maximum iterations"

    async def _execute_direct(self, task: str, context: dict | None = None) -> str:
        """Execute a task directly without LLM (deterministic)."""
        task_lower = task.lower()

        if any(kw in task_lower for kw in ["search", "find", "look for"]):
            query = self._extract_search_query(task)
            results = await self._search_tool(query)
            return f"Search results for '{query}':\n{results}"

        if any(kw in task_lower for kw in ["read", "show", "open", "file"]):
            path = self._extract_path(task)
            if path:
                return await self._read_file_tool(path)
            return "Please specify a file path to read."

        if any(kw in task_lower for kw in ["list", "files in", "directory"]):
            path = self._extract_path(task) or "."
            return await self._list_files_tool(path)

        if any(kw in task_lower for kw in ["run", "execute", "shell", "command"]):
            cmd = self._extract_shell_command(task)
            if cmd:
                return await self.tool_registry.execute("shell_exec", command=cmd)
            return "Please specify a command to run."

        if any(kw in task_lower for kw in ["git log", "commits", "history"]):
            return await self.tool_registry.execute("git_log")

        if any(kw in task_lower for kw in ["git diff", "changes", "diff"]):
            return await self.tool_registry.execute("git_diff")

        if any(kw in task_lower for kw in ["fetch", "http", "url", "download"]):
            url = self._extract_url(task)
            if url:
                return await self.tool_registry.execute("web_fetch", url=url)
            return "Please specify a URL to fetch."

        return (
            f"Task received: {task}\n\n"
            "I can help with:\n"
            "- Searching code (try: 'search for authentication functions')\n"
            "- Reading files (try: 'read backend/app/main.py')\n"
            "- Listing files (try: 'list files in backend/app/')\n"
            "- Shell commands (try: 'run ls -la')\n"
            "- Git log (try: 'show git log')\n"
            "- Git diff (try: 'show git diff')\n"
            "- Web fetch (try: 'fetch https://docs.python.org')"
        )

    def _extract_search_query(self, task: str) -> str:
        for prefix in ["search for", "find", "look for", "search", "find"]:
            if prefix in task.lower():
                idx = task.lower().index(prefix)
                return task[idx + len(prefix):].strip().strip("\"'")
        return task.strip()

    def _extract_path(self, task: str) -> str | None:
        match = re.search(r"[\w/.\-]+\.\w+", task)
        return match.group(0) if match else None

    def _extract_shell_command(self, task: str) -> str | None:
        for prefix in ["run ", "execute ", "shell ", "command "]:
            if prefix in task.lower():
                idx = task.lower().index(prefix)
                return task[idx + len(prefix):].strip().strip("\"'")
        return None

    def _extract_url(self, task: str) -> str | None:
        match = re.search(r"https?://[^\s]+", task)
        return match.group(0) if match else None

    async def _search_tool(self, query: str) -> str:
        if self._search_fn:
            try:
                results = await self._search_fn(query)
                if isinstance(results, dict):
                    results = results.get("results", [])
                lines = []
                for r in results[:10]:
                    rtype = r.get("type", "unknown")
                    name = r.get("name", r.get("file_path", "unknown"))
                    score = r.get("score", 0)
                    lines.append(f"  [{rtype}] {name} ({score:.2f})")
                return "\n".join(lines) if lines else "No results found"
            except Exception as e:
                return f"Search error: {e}"
        return "Search not available (no search function configured)"

    async def _read_file_tool(self, path: str) -> str:
        try:
            file_path = Path(path)
            if not file_path.exists():
                return f"File not found: {path}"
            content = file_path.read_text(encoding="utf-8", errors="replace")
            if len(content) > 10000:
                content = content[:10000] + f"\n... (truncated, {len(content)} total chars)"
            return content
        except Exception as e:
            return f"Error reading {path}: {e}"

    async def _write_file_tool(self, path: str, content: str = "") -> str:
        try:
            file_path = Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            return f"Written {len(content)} chars to {path}"
        except Exception as e:
            return f"Error writing {path}: {e}"

    async def _list_files_tool(self, path: str = ".") -> str:
        try:
            dir_path = Path(path)
            if not dir_path.is_dir():
                return f"Not a directory: {path}"
            entries = sorted(dir_path.iterdir(), key=lambda p: (not p.is_dir(), p.name))
            lines = []
            for entry in entries[:50]:
                suffix = "/" if entry.is_dir() else ""
                lines.append(f"  {entry.name}{suffix}")
            total = len(list(dir_path.iterdir()))
            if total > 50:
                lines.append(f"  ... and {total - 50} more")
            return "\n".join(lines) if lines else "Empty directory"
        except Exception as e:
            return f"Error listing {path}: {e}"
```

- [ ] **Step 6: Verify imports work**

```bash
cd /home/adi/Desktop/Cortex-Workspace
python -c "from backend.app.agents.tools import ToolRegistry; from backend.app.agents.tools.shell import ShellExecTool; from backend.app.agents.tools.git_tools import GitLogTool, GitDiffTool; from backend.app.agents.tools.web_fetch import WebFetchTool; r = ToolRegistry(); r.register(ShellExecTool()); r.register(GitLogTool()); r.register(GitDiffTool()); r.register(WebFetchTool()); print(r)"
```

- [ ] **Step 7: Commit**

```bash
git add backend/app/agents/tools/ backend/app/agents/executor.py
git commit -m "feat: expanded tool registry with shell, git, web fetch tools"
```

---

## Task 2: SSE Step Streaming

**Files:**
- Create: `backend/app/api/v1/agent_stream.py`
- Modify: `backend/app/agents/executor.py` (add event emission)
- Modify: `backend/app/agents/run_manager.py` (integrate SSE events)

- [ ] **Step 1: Create the SSE streaming endpoint**

```python
# backend/app/api/v1/agent_stream.py
"""
SSE endpoint for real-time agent step streaming.

Events emitted:
  - plan         — the agent's plan (array of steps)
  - step_start   — a step is beginning
  - step_output  — intermediate output from a step
  - step_complete — a step finished
  - run_complete — the entire run finished
  - error        — something went wrong
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.agents.executor import ExecutorAgent
from backend.app.agents.run_manager import AgentRunManager
from backend.app.core.db import get_current_user, get_db
from backend.app.models.agent import Agent, AgentRun, AgentStep
from backend.app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


class StreamRunPayload(BaseModel):
    agent_id: int
    input: str = Field(min_length=1)


class AgentEventEmitter:
    """Async event emitter that pushes SSE-formatted strings to a queue."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[str | None] = asyncio.Queue()

    async def emit(self, event: str, data: Any) -> None:
        """Emit an SSE event. data is JSON-serialised automatically."""
        payload = {
            "event": event,
            "data": data if isinstance(data, str) else json.dumps(data),
        }
        await self._queue.put(json.dumps(payload))

    async def done(self) -> None:
        """Signal the stream is finished."""
        await self._queue.put(None)

    async def stream(self):
        """Yield SSE-formatted lines until done."""
        while True:
            item = await self._queue.get()
            if item is None:
                break
            yield f"data: {item}\n\n"


async def _execute_streaming(
    agent: Agent,
    input_text: str,
    user_id: int,
    db: Session,
    emitter: AgentEventEmitter,
) -> None:
    """Run the agent and emit SSE events for each step."""
    manager = AgentRunManager(db)
    run = AgentRun(
        agent_id=agent.id,
        user_id=user_id,
        input_text=input_text,
        status="running",
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        # Step 1: Plan
        planner = manager.planner
        plan = await planner.plan(input_text)
        await emitter.emit("plan", {
            "run_id": run.id,
            "plan": plan,
            "total_steps": len(plan),
        })

        # Step 2: Execute each step with events
        executor = manager.executor
        results: list[str] = []

        for i, step_plan in enumerate(plan):
            step = AgentStep(
                run_id=run.id,
                step_number=i + 1,
                thought=step_plan.get("thought", ""),
                action=step_plan.get("agent", "executor"),
                action_input_json=json.dumps(step_plan),
                status="running",
            )
            db.add(step)
            db.commit()

            # Emit step_start
            await emitter.emit("step_start", {
                "run_id": run.id,
                "step_number": i + 1,
                "total_steps": len(plan),
                "action": step.action,
                "thought": step.thought,
                "goal": step_plan.get("goal", ""),
            })

            try:
                result = await executor.run(
                    step_plan.get("goal", ""),
                    context={"previous_steps": plan[:i], "previous_results": results},
                )
                step.observation = result
                step.status = "completed"
                results.append(result)

                # Emit step_output then step_complete
                await emitter.emit("step_output", {
                    "run_id": run.id,
                    "step_number": i + 1,
                    "output": result[:2000],  # truncate for SSE
                })
                await emitter.emit("step_complete", {
                    "run_id": run.id,
                    "step_number": i + 1,
                    "status": "completed",
                })
            except Exception as e:
                step.observation = f"Error: {e}"
                step.status = "failed"
                logger.error("Step %d failed: %s", i + 1, e)
                await emitter.emit("step_complete", {
                    "run_id": run.id,
                    "step_number": i + 1,
                    "status": "failed",
                    "error": str(e),
                })

            db.commit()

        # Finalize
        run.status = "completed"
        run.output = results[-1] if results else "No output"
        from datetime import datetime, timezone
        run.completed_at = datetime.now(timezone.utc)
        db.commit()

        await emitter.emit("run_complete", {
            "run_id": run.id,
            "status": "completed",
            "output": run.output[:2000] if run.output else None,
        })

    except Exception as e:
        run.status = "failed"
        run.error = str(e)
        from datetime import datetime, timezone
        run.completed_at = datetime.now(timezone.utc)
        db.commit()
        logger.error("Agent run %d failed: %s", run.id, e)
        await emitter.emit("error", {
            "run_id": run.id,
            "error": str(e),
        })

    finally:
        await emitter.done()


@router.post("/agents/stream")
async def stream_agent_run(
    payload: StreamRunPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """SSE endpoint — streams agent execution events in real-time.

    Returns a StreamingResponse with content-type text/event-stream.
    """
    manager = AgentRunManager(db)
    agent = manager.get_agent(payload.agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    emitter = AgentEventEmitter()

    # Launch the execution in a background task so we can return the stream immediately
    asyncio.create_task(
        _execute_streaming(agent, payload.input, current_user.id, db, emitter)
    )

    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        emitter.stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
```

- [ ] **Step 2: Register the streaming router in the API**

Find the main API router file (typically `backend/app/api/v1/__init__.py` or `backend/app/main.py`) and add:

```python
# In the router registration section, add:
from backend.app.api.v1.agent_stream import router as agent_stream_router
router.include_router(agent_stream_router, tags=["agent-stream"])
```

- [ ] **Step 3: Update AgentChat.tsx to use SSE**

```tsx
// frontend/app/agents/AgentChat.tsx — REPLACE entire file
"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import {
  Send,
  Bot,
  User,
  Loader2,
  ChevronDown,
  ChevronUp,
  Clock,
  Play,
  CheckCircle,
  XCircle,
  Radio,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "../../src/lib/utils";
import type { Agent, AgentRun, AgentStep } from "../../src/shared/types";
import { agentApi } from "../../src/shared/api/agent";

interface AgentChatProps {
  agent: Agent;
  onRunComplete?: (run: AgentRun) => void;
}

interface Message {
  role: "user" | "assistant" | "system";
  content: string;
  steps?: AgentStep[];
  timestamp?: string;
  streaming?: boolean;
}

interface StreamStep {
  step_number: number;
  action: string;
  thought: string;
  goal: string;
  status: "running" | "completed" | "failed";
  output?: string;
  error?: string;
}

const stepStatusIcons: Record<string, typeof Clock> = {
  pending: Clock,
  running: Play,
  completed: CheckCircle,
  failed: XCircle,
};

const stepStatusColors: Record<string, string> = {
  pending: "text-text-muted",
  running: "text-accent",
  completed: "text-success",
  failed: "text-error",
};

const stepStatusBg: Record<string, string> = {
  pending: "bg-bg-surface text-text-muted",
  running: "bg-accent/10 text-accent",
  completed: "bg-success/10 text-success",
  failed: "bg-error/10 text-error",
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "";

function getAuthToken(): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.split("; ").find((c) => c.startsWith("cortex_access="));
  return match ? match.split("=")[1] : null;
}

export default function AgentChat({ agent, onRunComplete }: AgentChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set());
  const [streamSteps, setStreamSteps] = useState<StreamStep[]>([]);
  const [streamOutput, setStreamOutput] = useState<string>("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamSteps]);

  function toggleStep(key: string) {
    setExpandedSteps((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  const sendStreaming = useCallback(
    async (userMessage: string) => {
      setLoading(true);
      setStreamSteps([]);
      setStreamOutput("");

      try {
        const token = getAuthToken();
        const response = await fetch(`${API_BASE}/api/v1/agents/stream`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          credentials: "include",
          body: JSON.stringify({ agent_id: agent.id, input: userMessage }),
        });

        if (!response.ok) {
          throw new Error(`Stream failed: ${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) throw new Error("No response body");

        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            const jsonStr = line.slice(6);
            try {
              const event = JSON.parse(jsonStr);
              const data = typeof event.data === "string" ? JSON.parse(event.data) : event.data;

              switch (event.event) {
                case "plan":
                  // Optionally show plan info
                  break;

                case "step_start":
                  setStreamSteps((prev) => [
                    ...prev,
                    {
                      step_number: data.step_number,
                      action: data.action,
                      thought: data.thought || "",
                      goal: data.goal || "",
                      status: "running",
                    },
                  ]);
                  break;

                case "step_output":
                  setStreamSteps((prev) =>
                    prev.map((s) =>
                      s.step_number === data.step_number ? { ...s, output: data.output } : s
                    )
                  );
                  break;

                case "step_complete":
                  setStreamSteps((prev) =>
                    prev.map((s) =>
                      s.step_number === data.step_number
                        ? { ...s, status: data.status, error: data.error }
                        : s
                    )
                  );
                  break;

                case "run_complete":
                  setStreamOutput(data.output || "");
                  const completedRun: AgentRun = {
                    id: data.run_id,
                    agent_id: agent.id,
                    user_id: 0,
                    input: userMessage,
                    status: "completed",
                    output: data.output,
                    error: null,
                    created_at: new Date().toISOString(),
                    completed_at: new Date().toISOString(),
                  };
                  setMessages((prev) => [
                    ...prev,
                    {
                      role: "assistant",
                      content: data.output || "No output",
                      steps: streamSteps.map((s) => ({
                        id: s.step_number,
                        run_id: data.run_id,
                        step_number: s.step_number,
                        thought: s.thought,
                        action: s.action,
                        action_input: null,
                        observation: s.output || null,
                        status: s.status,
                        created_at: null,
                      })),
                      timestamp: new Date().toISOString(),
                    },
                  ]);
                  onRunComplete?.(completedRun);
                  break;

                case "error":
                  setMessages((prev) => [
                    ...prev,
                    {
                      role: "assistant",
                      content: `Error: ${data.error}`,
                      timestamp: new Date().toISOString(),
                    },
                  ]);
                  break;
              }
            } catch {
              // Skip malformed JSON lines
            }
          }
        }
      } catch (err) {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: `Error: ${err instanceof Error ? err.message : "Stream failed"}`,
          },
        ]);
      } finally {
        setLoading(false);
        setStreamSteps([]);
      }
    },
    [agent.id, onRunComplete, streamSteps]
  );

  async function sendMessage() {
    if (!input.trim() || loading) return;
    const userMessage = input.trim();
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setInput("");
    await sendStreaming(userMessage);
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
        {messages.length === 0 && !loading && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <Bot className="h-12 w-12 text-accent/30 mb-3" />
            <p className="text-sm text-text-muted">
              Chat with <span className="font-medium text-text">{agent.name}</span>
            </p>
            <p className="text-xs text-text-muted/60 mt-1 max-w-xs">
              {agent.description || "Ask me anything about your codebase."}
            </p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={cn(
              "rounded-xl px-4 py-3 text-sm",
              msg.role === "user"
                ? "bg-accent/10 border border-accent/20 ml-8"
                : "bg-bg-elevated border border-border-subtle mr-8",
            )}
          >
            <div className="flex items-start gap-2">
              {msg.role === "assistant" && <Bot className="h-4 w-4 text-accent mt-0.5 shrink-0" />}
              {msg.role === "user" && <User className="h-4 w-4 text-accent mt-0.5 shrink-0" />}
              <div className="min-w-0 flex-1">
                <p className="text-text whitespace-pre-wrap">{msg.content}</p>
                {msg.steps && msg.steps.length > 0 && (
                  <div className="mt-3">
                    <button
                      onClick={() => toggleStep(`msg-${i}`)}
                      className="flex items-center gap-1.5 text-xs text-text-muted hover:text-accent transition-colors mb-2"
                    >
                      {expandedSteps.has(`msg-${i}`) ? (
                        <ChevronUp className="h-3 w-3" />
                      ) : (
                        <ChevronDown className="h-3 w-3" />
                      )}
                      {msg.steps.length} step{msg.steps.length > 1 ? "s" : ""}
                    </button>
                    <AnimatePresence>
                      {expandedSteps.has(`msg-${i}`) && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: "auto", opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.2, ease: "easeInOut" }}
                          className="overflow-hidden"
                        >
                          <div className="space-y-1.5 pl-1">
                            {msg.steps.map((step) => {
                              const StepIcon = stepStatusIcons[step.status] || Clock;
                              const stepKey = `msg-${i}-step-${step.id}`;
                              const isExpanded = expandedSteps.has(stepKey);
                              return (
                                <div
                                  key={step.id}
                                  className="rounded-lg border border-border-subtle bg-bg-surface/50 overflow-hidden"
                                >
                                  <button
                                    onClick={() => toggleStep(stepKey)}
                                    className="w-full flex items-center gap-2 px-3 py-2 text-xs hover:bg-bg-hover/50 transition-colors"
                                  >
                                    <span className="font-mono text-text-muted w-5 text-right shrink-0">
                                      {step.step_number}.
                                    </span>
                                    <StepIcon
                                      className={cn(
                                        "h-3.5 w-3.5 shrink-0",
                                        stepStatusColors[step.status],
                                      )}
                                    />
                                    <span className="font-medium text-text truncate flex-1 text-left">
                                      {step.action}
                                    </span>
                                    <span
                                      className={cn(
                                        "px-1.5 py-0.5 rounded text-[10px] font-mono shrink-0",
                                        stepStatusBg[step.status],
                                      )}
                                    >
                                      {step.status}
                                    </span>
                                    {isExpanded ? (
                                      <ChevronUp className="h-3 w-3 text-text-muted shrink-0" />
                                    ) : (
                                      <ChevronDown className="h-3 w-3 text-text-muted shrink-0" />
                                    )}
                                  </button>
                                  <AnimatePresence>
                                    {isExpanded && (
                                      <motion.div
                                        initial={{ height: 0, opacity: 0 }}
                                        animate={{ height: "auto", opacity: 1 }}
                                        exit={{ height: 0, opacity: 0 }}
                                        transition={{ duration: 0.15 }}
                                        className="overflow-hidden"
                                      >
                                        <div className="px-3 pb-2.5 pt-0.5 space-y-1.5">
                                          {step.thought && (
                                            <div className="flex items-start gap-2">
                                              <span className="text-[10px] font-mono text-text-muted uppercase shrink-0 mt-0.5">
                                                thought
                                              </span>
                                              <p className="text-text-muted/70 text-[11px] leading-relaxed">
                                                {step.thought}
                                              </p>
                                            </div>
                                          )}
                                          {step.observation && (
                                            <div className="flex items-start gap-2">
                                              <span className="text-[10px] font-mono text-text-muted uppercase shrink-0 mt-0.5">
                                                output
                                              </span>
                                              <p className="text-text-secondary font-mono text-[11px] leading-relaxed">
                                                {step.observation.slice(0, 300)}
                                                {step.observation.length > 300 && "..."}
                                              </p>
                                            </div>
                                          )}
                                        </div>
                                      </motion.div>
                                    )}
                                  </AnimatePresence>
                                </div>
                              );
                            })}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                )}
                {msg.timestamp && (
                  <p className="text-[10px] text-text-muted/40 mt-2">
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </p>
                )}
              </div>
            </div>
          </div>
        ))}

        {/* Live streaming steps */}
        {loading && streamSteps.length > 0 && (
          <div className="bg-bg-elevated border border-accent/20 rounded-xl px-4 py-3 mr-8">
            <div className="flex items-center gap-2 text-xs text-accent mb-2">
              <Radio className="h-3 w-3 animate-pulse" />
              <span className="font-medium">Executing steps...</span>
            </div>
            <div className="space-y-1.5">
              {streamSteps.map((step) => {
                const StepIcon = stepStatusIcons[step.status] || Clock;
                return (
                  <div
                    key={step.step_number}
                    className="flex items-center gap-2 text-xs px-2 py-1.5 rounded-lg bg-bg-surface/50"
                  >
                    <span className="font-mono text-text-muted w-5 text-right shrink-0">
                      {step.step_number}.
                    </span>
                    <StepIcon
                      className={cn("h-3.5 w-3.5 shrink-0", stepStatusColors[step.status])}
                    />
                    <span className="text-text truncate flex-1">{step.goal || step.action}</span>
                    <span
                      className={cn(
                        "px-1.5 py-0.5 rounded text-[10px] font-mono shrink-0",
                        stepStatusBg[step.status],
                      )}
                    >
                      {step.status}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {loading && streamSteps.length === 0 && (
          <div className="bg-bg-elevated border border-border-subtle rounded-xl px-4 py-3 mr-8 animate-pulse">
            <div className="flex items-center gap-2 text-sm text-text-muted">
              <Loader2 className="h-4 w-4 animate-spin" />
              Planning...
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="shrink-0 px-4 py-3 border-t border-border-subtle bg-bg-elevated/30">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask the agent..."
            disabled={loading}
            className="flex-1 rounded-xl bg-bg-surface border border-border-subtle px-4 py-2.5 text-sm text-text placeholder:text-text-muted outline-none transition-all duration-200 focus:border-accent/40 focus:ring-2 focus:ring-accent/10 disabled:opacity-50"
          />
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            className={cn(
              "rounded-xl px-4 py-2.5 text-sm font-medium transition-all duration-200",
              loading || !input.trim()
                ? "bg-bg-surface text-text-muted border border-border-subtle"
                : "bg-accent text-black hover:bg-accent-hover",
            )}
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Verify SSE endpoint works**

```bash
cd /home/adi/Desktop/Cortex-Workspace
# Start the backend, then:
curl -N -X POST http://localhost:8000/api/v1/agents/stream \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"agent_id": 1, "input": "list files in backend/app"}'
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/v1/agent_stream.py frontend/app/agents/AgentChat.tsx
git commit -m "feat: real-time agent step streaming via SSE"
```

---

## Task 3: Agent Metrics

**Files:**
- Create: `backend/app/services/agent_metrics.py`
- Create: `backend/app/api/v1/agent_metrics.py`

- [ ] **Step 1: Create the in-memory metrics service**

```python
# backend/app/services/agent_metrics.py
"""
Agent metrics — tracks per-agent performance data.

Stores metrics in-memory for now. Persist to DB in a future phase.
Thread-safe via asyncio.Lock for the async FastAPI context.
"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentMetricsSnapshot:
    """Aggregated metrics for a single agent."""
    agent_id: int
    agent_name: str
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    success_rate: float = 0.0
    avg_duration_seconds: float = 0.0
    total_duration_seconds: float = 0.0
    avg_steps_per_run: float = 0.0
    total_steps: int = 0
    total_tokens_used: int = 0
    avg_tokens_per_run: float = 0.0
    tool_usage: dict[str, int] = field(default_factory=dict)
    last_run_at: str | None = None


@dataclass
class _RunRecord:
    """Internal record for a single run."""
    agent_id: int
    agent_name: str
    user_id: int
    status: str
    start_time: float
    end_time: float | None = None
    duration_seconds: float = 0.0
    steps_count: int = 0
    tokens_used: int = 0
    tools_used: list[str] = field(default_factory=list)


class AgentMetricsService:
    """In-memory agent metrics tracker.

    Usage:
        metrics = AgentMetricsService()
        metrics.record_run_start(agent_id=1, agent_name="Executor", user_id=42)
        metrics.record_run_end(agent_id=1, run_id=100, status="completed", duration=2.5, steps=3)
        snapshot = metrics.get_agent_metrics(agent_id=1, agent_name="Executor")
    """

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._runs: list[_RunRecord] = []
        self._tool_counts: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._total_tokens: dict[int, int] = defaultdict(int)

    async def record_run_start(
        self,
        agent_id: int,
        agent_name: str,
        user_id: int,
    ) -> None:
        """Record that a run has started."""
        async with self._lock:
            record = _RunRecord(
                agent_id=agent_id,
                agent_name=agent_name,
                user_id=user_id,
                status="running",
                start_time=time.time(),
            )
            self._runs.append(record)

    async def record_run_end(
        self,
        agent_id: int,
        run_id: int,
        status: str,
        duration: float,
        steps: int = 0,
        tokens_used: int = 0,
        tools_used: list[str] | None = None,
    ) -> None:
        """Record that a run has finished."""
        async with self._lock:
            # Find the running record for this agent
            for record in reversed(self._runs):
                if record.agent_id == agent_id and record.status == "running":
                    record.status = status
                    record.end_time = time.time()
                    record.duration_seconds = duration
                    record.steps_count = steps
                    record.tokens_used = tokens_used
                    if tools_used:
                        record.tools_used = tools_used
                        for tool in tools_used:
                            self._tool_counts[agent_id][tool] += 1
                    if tokens_used:
                        self._total_tokens[agent_id] += tokens_used
                    break

    async def record_tool_use(self, agent_id: int, tool_name: str) -> None:
        """Record a single tool invocation."""
        async with self._lock:
            self._tool_counts[agent_id][tool_name] += 1

    async def get_agent_metrics(
        self,
        agent_id: int,
        agent_name: str = "",
    ) -> AgentMetricsSnapshot:
        """Get aggregated metrics for a single agent."""
        async with self._lock:
            agent_runs = [r for r in self._runs if r.agent_id == agent_id]
            completed = [r for r in agent_runs if r.status == "completed"]
            failed = [r for r in agent_runs if r.status == "failed"]
            total = len(agent_runs)

            durations = [r.duration_seconds for r in agent_runs if r.duration_seconds > 0]
            steps_list = [r.steps_count for r in agent_runs if r.steps_count > 0]
            tokens_list = [r.tokens_used for r in agent_runs if r.tokens_used > 0]

            last_run = agent_runs[-1] if agent_runs else None

            return AgentMetricsSnapshot(
                agent_id=agent_id,
                agent_name=agent_name or (last_run.agent_name if last_run else ""),
                total_runs=total,
                successful_runs=len(completed),
                failed_runs=len(failed),
                success_rate=len(completed) / total if total > 0 else 0.0,
                avg_duration_seconds=sum(durations) / len(durations) if durations else 0.0,
                total_duration_seconds=sum(durations),
                avg_steps_per_run=sum(steps_list) / len(steps_list) if steps_list else 0.0,
                total_steps=sum(steps_list),
                total_tokens_used=sum(tokens_list),
                avg_tokens_per_run=sum(tokens_list) / len(tokens_list) if tokens_list else 0.0,
                tool_usage=dict(self._tool_counts.get(agent_id, {})),
                last_run_at=last_run.end_time and time.strftime(
                    "%Y-%m-%dT%H:%M:%SZ", time.gmtime(last_run.end_time)
                ),
            )

    async def get_all_metrics(self, agents: list[tuple[int, str]] | None = None) -> list[AgentMetricsSnapshot]:
        """Get metrics for all known agents.

        Args:
            agents: list of (agent_id, agent_name) tuples. If None, derives from recorded runs.
        """
        async with self._lock:
            if agents is None:
                seen: dict[int, str] = {}
                for r in self._runs:
                    seen[r.agent_id] = r.agent_name
                agents = list(seen.items())

        snapshots = []
        for agent_id, agent_name in agents:
            snapshot = await self.get_agent_metrics(agent_id, agent_name)
            snapshots.append(snapshot)
        return snapshots

    async def get_global_metrics(self) -> dict[str, Any]:
        """Get system-wide agent metrics."""
        async with self._lock:
            total_runs = len(self._runs)
            completed = sum(1 for r in self._runs if r.status == "completed")
            failed = sum(1 for r in self._runs if r.status == "failed")
            durations = [r.duration_seconds for r in self._runs if r.duration_seconds > 0]
            all_tools: dict[str, int] = defaultdict(int)
            for tool_counts in self._tool_counts.values():
                for tool, count in tool_counts.items():
                    all_tools[tool] += count

            return {
                "total_runs": total_runs,
                "successful_runs": completed,
                "failed_runs": failed,
                "success_rate": completed / total_runs if total_runs > 0 else 0.0,
                "avg_duration_seconds": sum(durations) / len(durations) if durations else 0.0,
                "total_tokens_used": sum(self._total_tokens.values()),
                "tool_usage": dict(all_tools),
            }
```

- [ ] **Step 2: Create the metrics API endpoints**

```python
# backend/app/api/v1/agent_metrics.py
"""
Agent metrics API — exposes per-agent and global performance metrics.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.agents.run_manager import AgentRunManager
from backend.app.core.db import get_current_user, get_db
from backend.app.models.user import User
from backend.app.services.agent_metrics import AgentMetricsService

router = APIRouter()

# Singleton metrics service (in-memory, resets on server restart)
_metrics_service = AgentMetricsService()


def get_metrics_service() -> AgentMetricsService:
    """Dependency that returns the metrics service singleton."""
    return _metrics_service


@router.get("/agents/metrics")
async def get_all_agent_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    metrics: AgentMetricsService = Depends(get_metrics_service),
):
    """Get metrics for all agents."""
    manager = AgentRunManager(db)
    agents = manager.list_agents(active_only=False)
    agent_pairs = [(a.id, a.name) for a in agents]
    snapshots = await metrics.get_all_metrics(agent_pairs)
    return {
        "metrics": [
            {
                "agent_id": s.agent_id,
                "agent_name": s.agent_name,
                "total_runs": s.total_runs,
                "successful_runs": s.successful_runs,
                "failed_runs": s.failed_runs,
                "success_rate": round(s.success_rate, 3),
                "avg_duration_seconds": round(s.avg_duration_seconds, 2),
                "total_duration_seconds": round(s.total_duration_seconds, 2),
                "avg_steps_per_run": round(s.avg_steps_per_run, 1),
                "total_steps": s.total_steps,
                "total_tokens_used": s.total_tokens_used,
                "avg_tokens_per_run": round(s.avg_tokens_per_run, 0),
                "tool_usage": s.tool_usage,
                "last_run_at": s.last_run_at,
            }
            for s in snapshots
        ]
    }


@router.get("/agents/metrics/{agent_id}")
async def get_agent_metrics(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    metrics: AgentMetricsService = Depends(get_metrics_service),
):
    """Get metrics for a specific agent."""
    manager = AgentRunManager(db)
    agent = manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    snapshot = await metrics.get_agent_metrics(agent_id, agent.name)
    return {
        "agent_id": snapshot.agent_id,
        "agent_name": snapshot.agent_name,
        "total_runs": snapshot.total_runs,
        "successful_runs": snapshot.successful_runs,
        "failed_runs": snapshot.failed_runs,
        "success_rate": round(snapshot.success_rate, 3),
        "avg_duration_seconds": round(snapshot.avg_duration_seconds, 2),
        "total_duration_seconds": round(snapshot.total_duration_seconds, 2),
        "avg_steps_per_run": round(snapshot.avg_steps_per_run, 1),
        "total_steps": snapshot.total_steps,
        "total_tokens_used": snapshot.total_tokens_used,
        "avg_tokens_per_run": round(snapshot.avg_tokens_per_run, 0),
        "tool_usage": snapshot.tool_usage,
        "last_run_at": snapshot.last_run_at,
    }


@router.get("/agents/metrics/global/summary")
async def get_global_metrics(
    current_user: User = Depends(get_current_user),
    metrics: AgentMetricsService = Depends(get_metrics_service),
):
    """Get system-wide agent metrics summary."""
    summary = await metrics.get_global_metrics()
    return summary


@router.post("/agents/metrics/record")
async def record_run_metrics(
    agent_id: int,
    run_id: int,
    status: str,
    duration: float,
    steps: int = 0,
    tokens_used: int = 0,
    tools_used: list[str] | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    metrics: AgentMetricsService = Depends(get_metrics_service),
):
    """Manually record metrics for a run (used internally by run_manager)."""
    manager = AgentRunManager(db)
    agent = manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    await metrics.record_run_end(
        agent_id=agent_id,
        run_id=run_id,
        status=status,
        duration=duration,
        steps=steps,
        tokens_used=tokens_used,
        tools_used=tools_used or [],
    )
    return {"status": "recorded"}
```

- [ ] **Step 3: Register the metrics router**

Find the main API router file and add:

```python
# In the router registration section, add:
from backend.app.api.v1.agent_metrics import router as agent_metrics_router
router.include_router(agent_metrics_router, tags=["agent-metrics"])
```

- [ ] **Step 4: Integrate metrics recording into run_manager.py**

Add these lines to the `run_agent` method in `backend/app/agents/run_manager.py`. Insert after `run = AgentRun(...)` is committed and before the try block, and update the finally/except blocks:

```python
# At the top of run_manager.py, add import:
from backend.app.services.agent_metrics import AgentMetricsService

# In the AgentRunManager class, add a metrics_service attribute:
class AgentRunManager:
    def __init__(self, db, planner=None, executor=None):
        self.db = db
        self.planner = planner or PlannerAgent()
        self.executor = executor or ExecutorAgent()
        self.metrics_service = AgentMetricsService()  # ADD THIS LINE

# In the run_agent method, after creating the run record, add:
        # Record run start
        await self.metrics_service.record_run_start(
            agent_id=agent_id,
            agent_name=agent.name,
            user_id=user_id,
        )

# In the success block (after run.status = "completed"), add:
            # Record metrics
            import time
            duration = time.time() - run_start_time  # You'll need to capture this
            await self.metrics_service.record_run_end(
                agent_id=agent_id,
                run_id=run.id,
                status="completed",
                duration=duration,
                steps=len(plan),
                tools_used=[],  # Could track this if needed
            )

# In the exception block (after run.status = "failed"), add:
            import time
            duration = time.time() - run_start_time
            await self.metrics_service.record_run_end(
                agent_id=agent_id,
                run_id=run.id,
                status="failed",
                duration=duration,
                steps=0,
            )
```

- [ ] **Step 5: Verify metrics endpoints**

```bash
cd /home/adi/Desktop/Cortex-Workspace
# Start the backend, then:
curl http://localhost:8000/api/v1/agents/metrics \
  -H "Authorization: Bearer <token>"
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/agent_metrics.py backend/app/api/v1/agent_metrics.py backend/app/agents/run_manager.py
git commit -m "feat: agent performance metrics with in-memory tracking"
```

---

## Task 4: Frontend Agent Dashboard

**Files:**
- Create: `frontend/app/agents/AgentDashboard.tsx`
- Create: `frontend/src/shared/api/agentMetrics.ts`
- Modify: `frontend/app/agents/page.tsx` (add dashboard link)
- Modify: `frontend/src/shared/types.ts` (add AgentMetrics type)

- [ ] **Step 1: Add AgentMetrics type to shared types**

```typescript
// frontend/src/shared/types.ts — APPEND to end of file

// ── Agent Metrics ──────────────────────────────────────────────

export interface AgentMetrics {
  agent_id: number;
  agent_name: string;
  total_runs: number;
  successful_runs: number;
  failed_runs: number;
  success_rate: number;
  avg_duration_seconds: number;
  total_duration_seconds: number;
  avg_steps_per_run: number;
  total_steps: number;
  total_tokens_used: number;
  avg_tokens_per_run: number;
  tool_usage: Record<string, number>;
  last_run_at: string | null;
}

export interface AgentMetricsListResponse {
  metrics: AgentMetrics[];
}

export interface AgentMetricsDetailResponse {
  agent_id: number;
  agent_name: string;
  total_runs: number;
  successful_runs: number;
  failed_runs: number;
  success_rate: number;
  avg_duration_seconds: number;
  total_duration_seconds: number;
  avg_steps_per_run: number;
  total_steps: number;
  total_tokens_used: number;
  avg_tokens_per_run: number;
  tool_usage: Record<string, number>;
  last_run_at: string | null;
}

export interface GlobalMetricsResponse {
  total_runs: number;
  successful_runs: number;
  failed_runs: number;
  success_rate: number;
  avg_duration_seconds: number;
  total_tokens_used: number;
  tool_usage: Record<string, number>;
}
```

- [ ] **Step 2: Create the agent metrics API client**

```typescript
// frontend/src/shared/api/agentMetrics.ts

import { api } from "./client";
import type {
  AgentMetricsListResponse,
  AgentMetricsDetailResponse,
  GlobalMetricsResponse,
} from "../types";

export const agentMetricsApi = {
  /** Get metrics for all agents. */
  list: (): Promise<AgentMetricsListResponse> => {
    return api.get("/api/v1/agents/metrics");
  },

  /** Get metrics for a specific agent. */
  get: (agentId: number): Promise<AgentMetricsDetailResponse> => {
    return api.get(`/api/v1/agents/metrics/${agentId}`);
  },

  /** Get global metrics summary. */
  global: (): Promise<GlobalMetricsResponse> => {
    return api.get("/api/v1/agents/metrics/global/summary");
  },
};
```

- [ ] **Step 3: Create the AgentDashboard component**

```tsx
// frontend/app/agents/AgentDashboard.tsx
"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  BarChart3,
  ArrowLeft,
  CheckCircle,
  XCircle,
  Clock,
  Zap,
  Activity,
  Bot,
} from "lucide-react";
import { motion } from "framer-motion";
import DashboardShell from "../../src/shared/layout/DashboardShell";
import Button from "../../src/shared/ui/Button";
import NeuralNetwork from "../../src/shared/ui/NeuralNetwork";
import { agentMetricsApi } from "../../src/shared/api/agentMetrics";
import { agentApi } from "../../src/shared/api/agent";
import { useAuth } from "../../src/shared/auth/AuthProvider";
import { cn } from "../../src/lib/utils";
import type { Agent, AgentMetrics, GlobalMetricsResponse } from "../../src/shared/types";

function MetricCard({
  label,
  value,
  icon: Icon,
  color,
  sub,
}: {
  label: string;
  value: string | number;
  icon: typeof Clock;
  color: string;
  sub?: string;
}) {
  return (
    <div className="rounded-xl border border-border-subtle bg-bg-elevated p-4">
      <div className="flex items-center gap-2 mb-2">
        <div className={cn("h-7 w-7 rounded-lg flex items-center justify-center", color)}>
          <Icon className="h-3.5 w-3.5" />
        </div>
        <span className="text-[10px] font-mono text-text-muted uppercase tracking-wider">
          {label}
        </span>
      </div>
      <p className="text-2xl font-bold text-text font-mono">{value}</p>
      {sub && <p className="text-[10px] text-text-muted mt-1">{sub}</p>}
    </div>
  );
}

function AgentPerformanceCard({ metrics }: { metrics: AgentMetrics }) {
  const successPercent = Math.round(metrics.success_rate * 100);
  const toolEntries = Object.entries(metrics.tool_usage).sort((a, b) => b[1] - a[1]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl border border-border-subtle bg-bg-elevated p-5"
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Bot className="h-4 w-4 text-accent" />
          <h3 className="text-sm font-semibold text-text">{metrics.agent_name}</h3>
        </div>
        <span className="text-[10px] font-mono text-text-muted">
          {metrics.total_runs} runs
        </span>
      </div>

      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="text-center">
          <p className="text-lg font-bold text-success font-mono">{successPercent}%</p>
          <p className="text-[10px] text-text-muted">Success</p>
        </div>
        <div className="text-center">
          <p className="text-lg font-bold text-accent font-mono">
            {metrics.avg_duration_seconds.toFixed(1)}s
          </p>
          <p className="text-[10px] text-text-muted">Avg Duration</p>
        </div>
        <div className="text-center">
          <p className="text-lg font-bold text-text font-mono">
            {metrics.avg_steps_per_run.toFixed(1)}
          </p>
          <p className="text-[10px] text-text-muted">Avg Steps</p>
        </div>
      </div>

      {/* Success bar */}
      <div className="mb-4">
        <div className="flex justify-between text-[10px] text-text-muted mb-1">
          <span>Success Rate</span>
          <span>
            {metrics.successful_runs}/{metrics.total_runs}
          </span>
        </div>
        <div className="h-1.5 bg-bg-surface rounded-full overflow-hidden">
          <div
            className="h-full bg-success rounded-full transition-all duration-500"
            style={{ width: `${successPercent}%` }}
          />
        </div>
      </div>

      {/* Tool usage */}
      {toolEntries.length > 0 && (
        <div>
          <p className="text-[10px] font-mono text-text-muted uppercase tracking-wider mb-2">
            Tool Usage
          </p>
          <div className="flex flex-wrap gap-1.5">
            {toolEntries.slice(0, 6).map(([tool, count]) => (
              <span
                key={tool}
                className="px-2 py-0.5 rounded-md bg-bg-surface border border-border-subtle text-[10px] font-mono text-text-secondary"
              >
                {tool}: {count}
              </span>
            ))}
          </div>
        </div>
      )}

      {metrics.last_run_at && (
        <p className="text-[10px] text-text-muted/40 mt-3">
          Last run: {new Date(metrics.last_run_at).toLocaleString()}
        </p>
      )}
    </motion.div>
  );
}

export default function AgentDashboard() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [metricsList, setMetricsList] = useState<AgentMetrics[]>([]);
  const [globalMetrics, setGlobalMetrics] = useState<GlobalMetricsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!authLoading && !user) router.replace("/auth");
  }, [authLoading, user, router]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [metricsData, globalData] = await Promise.all([
        agentMetricsApi.list(),
        agentMetricsApi.global(),
      ]);
      setMetricsList(metricsData.metrics);
      setGlobalMetrics(globalData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load metrics");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return (
    <DashboardShell>
      <NeuralNetwork intensity="low" />
      <div className="flex flex-col h-full bg-transparent p-6 overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.push("/agents")}
              className="h-8 w-8 rounded-lg bg-bg-elevated border border-border-subtle flex items-center justify-center hover:border-accent/30 transition-colors"
            >
              <ArrowLeft className="h-4 w-4 text-text-muted" />
            </button>
            <div>
              <h1 className="text-lg font-semibold text-text flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-accent" />
                Agent Dashboard
              </h1>
              <p className="text-xs text-text-muted">Performance metrics and analytics</p>
            </div>
          </div>
          <Button variant="secondary" onClick={fetchData} size="sm">
            Refresh
          </Button>
        </div>

        {error && (
          <div className="rounded-xl border border-error/20 bg-error/5 px-4 py-3 text-sm text-error mb-4">
            {error}
          </div>
        )}

        {/* Global Summary */}
        {loading ? (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-24 animate-pulse rounded-xl bg-bg-elevated border border-border-subtle" />
            ))}
          </div>
        ) : globalMetrics ? (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
            <MetricCard
              label="Total Runs"
              value={globalMetrics.total_runs}
              icon={Activity}
              color="bg-accent/10 text-accent"
              sub={`${globalMetrics.successful_runs} succeeded`}
            />
            <MetricCard
              label="Success Rate"
              value={`${Math.round(globalMetrics.success_rate * 100)}%`}
              icon={CheckCircle}
              color="bg-success/10 text-success"
              sub={`${globalMetrics.failed_runs} failed`}
            />
            <MetricCard
              label="Avg Duration"
              value={`${globalMetrics.avg_duration_seconds.toFixed(1)}s`}
              icon={Clock}
              color="bg-warning/10 text-warning"
            />
            <MetricCard
              label="Total Tokens"
              value={globalMetrics.total_tokens_used.toLocaleString()}
              icon={Zap}
              color="bg-purple-500/10 text-purple-400"
            />
          </div>
        ) : null}

        {/* Per-Agent Cards */}
        <div className="mb-4">
          <h2 className="text-sm font-semibold text-text mb-1">Agent Performance</h2>
          <p className="text-xs text-text-muted">Individual agent metrics and tool usage</p>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-48 animate-pulse rounded-xl bg-bg-elevated border border-border-subtle" />
            ))}
          </div>
        ) : metricsList.length === 0 ? (
          <div className="text-center py-12">
            <Bot className="h-12 w-12 text-text-muted/30 mx-auto mb-3" />
            <p className="text-sm text-text-muted">No agent metrics yet</p>
            <p className="text-xs text-text-muted/60 mt-1">Run some agents to see performance data</p>
            <Button onClick={() => router.push("/agents")} className="mt-4" size="sm">
              Go to Agents
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {metricsList.map((m) => (
              <AgentPerformanceCard key={m.agent_id} metrics={m} />
            ))}
          </div>
        )}

        {/* Global Tool Usage */}
        {globalMetrics && Object.keys(globalMetrics.tool_usage).length > 0 && (
          <div className="mt-6">
            <h2 className="text-sm font-semibold text-text mb-3">Global Tool Usage</h2>
            <div className="rounded-xl border border-border-subtle bg-bg-elevated p-4">
              <div className="flex flex-wrap gap-2">
                {Object.entries(globalMetrics.tool_usage)
                  .sort((a, b) => b[1] - a[1])
                  .map(([tool, count]) => {
                    const maxCount = Math.max(...Object.values(globalMetrics.tool_usage));
                    const width = Math.max(20, (count / maxCount) * 100);
                    return (
                      <div key={tool} className="flex items-center gap-2 min-w-[140px]">
                        <span className="text-xs font-mono text-text-secondary w-24 truncate">
                          {tool}
                        </span>
                        <div className="flex-1 h-2 bg-bg-surface rounded-full overflow-hidden">
                          <div
                            className="h-full bg-accent/60 rounded-full"
                            style={{ width: `${width}%` }}
                          />
                        </div>
                        <span className="text-[10px] font-mono text-text-muted w-8 text-right">
                          {count}
                        </span>
                      </div>
                    );
                  })}
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardShell>
  );
}
```

- [ ] **Step 4: Add dashboard link to the agents page**

In `frontend/app/agents/page.tsx`, add the import and a button in the header area. Add these changes:

```tsx
// Add import at the top (after existing imports):
import { BarChart3 } from "lucide-react";

// In the CollapsiblePanel header section, after the "Agent List" label and the Plus button,
// add a dashboard link button. Find the div with className="flex items-center justify-between mb-3"
// and modify it to:

            <div className="flex items-center justify-between mb-3">
              <span className="text-[10px] font-mono font-bold text-text-muted uppercase tracking-wider px-1">
                Agent List
              </span>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => router.push("/agents/dashboard")}
                  className="h-7 w-7 rounded-lg bg-bg-surface border border-border-subtle flex items-center justify-center hover:border-accent/30 transition-colors"
                  title="Agent Dashboard"
                >
                  <BarChart3 className="h-3.5 w-3.5 text-text-muted" />
                </button>
                <Button onClick={() => setShowCreate(true)} size="sm">
                  <Plus className="h-3.5 w-3.5" />
                </Button>
              </div>
            </div>
```

- [ ] **Step 5: Create the dashboard page route**

```tsx
// frontend/app/agents/dashboard/page.tsx
"use client";

import AgentDashboard from "../AgentDashboard";

export default function DashboardPage() {
  return <AgentDashboard />;
}
```

- [ ] **Step 6: Verify frontend builds**

```bash
cd /home/adi/Desktop/Cortex-Workspace/frontend
npm run build
```

- [ ] **Step 7: Commit**

```bash
git add frontend/app/agents/AgentDashboard.tsx frontend/app/agents/dashboard/page.tsx frontend/app/agents/page.tsx frontend/src/shared/api/agentMetrics.ts frontend/src/shared/types.ts
git commit -m "feat: agent performance dashboard with metrics cards"
```

---

## Exit Criteria

- [ ] Shell, git, and web fetch tools are registered and callable via `ToolRegistry`
- [ ] SSE streaming endpoint emits `plan`, `step_start`, `step_output`, `step_complete`, `run_complete`, `error` events
- [ ] Frontend AgentChat uses SSE for real-time step visualization
- [ ] Agent metrics are tracked per-agent (runs, success rate, duration, tool usage)
- [ ] Dashboard shows global summary + per-agent performance cards
- [ ] All Python imports resolve, frontend builds clean
