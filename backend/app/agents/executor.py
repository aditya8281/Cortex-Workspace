"""Executor agent — completes tasks using available tools."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import secrets
import time
from typing import Any

from backend.app.agents.base import BaseAgent
from backend.app.agents.tool_defs import (
    TOOL_REGISTRY,
    requires_approval,
)

logger = logging.getLogger(__name__)

EXECUTOR_SYSTEM_PROMPT = """You are an executor agent for a code intelligence system.
You complete tasks by using available tools: search, read_file, write_file, and list_files.

When given a task:
1. Think about what tools you need
2. Use the tools to gather information or make changes
3. Report your results

Always explain what you did and what you found."""


class ExecutorAgent(BaseAgent):
    """Executes tasks using available tools."""

    def __init__(
        self,
        search_fn: Any | None = None,
        llm_chat: Any | None = None,
        agent: Any | None = None,
    ):
        super().__init__(system_prompt=EXECUTOR_SYSTEM_PROMPT)
        self._search_fn = search_fn
        self._llm_chat = llm_chat
        self._agent = agent
        self._approved_tools: set[str] = set()
        self._approval_secret = secrets.token_hex(32)

        self.register_tool("search", self._search_tool)
        self.register_tool("read_file", self._read_file_tool)
        self.register_tool("write_file", self._write_file_tool)
        self.register_tool("list_files", self._list_files_tool)

        for name, entry in TOOL_REGISTRY.items():
            self.register_tool(name, entry["handler"])

    def _generate_approval_token(self, tool_name: str, user_id: int) -> str:
        """Generate an HMAC-signed approval token for a tool."""
        payload = f"{tool_name}:{user_id}:{int(time.time())}"
        signature = hmac.new(self._approval_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        return f"{payload}:{signature}"

    def _verify_approval_token(self, token: str, tool_name: str, user_id: int) -> bool:
        """Verify an HMAC-signed approval token."""
        try:
            parts = token.split(":")
            if len(parts) != 4:
                return False
            t_tool, t_user, t_ts, t_sig = parts
            if t_tool != tool_name or int(t_user) != user_id:
                return False
            # Check token age (max 5 minutes)
            if time.time() - int(t_ts) > 300:
                return False
            expected = hmac.new(
                self._approval_secret.encode(),
                f"{t_tool}:{t_user}:{t_ts}".encode(),
                hashlib.sha256,
            ).hexdigest()
            return hmac.compare_digest(expected, t_sig)
        except (ValueError, TypeError):
            return False

    def approve_tool(self, tool_name: str, user_id: int | None = None) -> str:
        """Approve a tool for execution. Returns a signed token that must be
        presented to actually execute the tool. If user_id is provided, generates
        an HMAC-signed token; otherwise falls back to in-process approval (legacy)."""
        if user_id is not None:
            self._approved_tools.add(tool_name)
            return self._generate_approval_token(tool_name, user_id)
        self._approved_tools.add(tool_name)
        return ""

    async def execute_tool(self, name: str, **kwargs: Any) -> Any:
        # Block approve_tool from being called via LLM tool-calling
        if name == "approve_tool":
            return "Error: approve_tool cannot be called via tool calling. Human approval required."
        # Verify HMAC token if present in kwargs
        approval_token = kwargs.pop("_approval_token", None)
        if requires_approval(name):
            if approval_token:
                user_id = kwargs.get("_user_id")
                if user_id is None or not self._verify_approval_token(approval_token, name, int(user_id)):
                    return f"Tool '{name}' requires valid approval token."
            elif name not in self._approved_tools:
                return f"Tool '{name}' requires approval. Call approve_tool('{name}') first."
        return await super().execute_tool(name, **kwargs)

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
            messages.append(
                {
                    "role": "user",
                    "content": f"Context from previous steps:\n{context}",
                }
            )

        # Filter tools based on agent's allowed tools_json
        all_schemas = self.get_tool_schemas()
        allowed_tools = None
        if self._agent and getattr(self._agent, "tools_json", None):
            try:
                allowed_tools = json.loads(self._agent.tools_json)
            except (json.JSONDecodeError, TypeError):
                pass
        if allowed_tools:
            all_schemas = [s for s in all_schemas if s["function"]["name"] in allowed_tools]

        max_iterations = 10
        for _ in range(max_iterations):
            try:
                result = await self._llm_chat(messages, all_schemas)
                text = result[0] if isinstance(result, tuple) else str(result)

                # Check for tool calls
                if isinstance(result, tuple) and len(result) > 1 and result[1]:
                    tool_calls = result[1]
                    for call in tool_calls:
                        tool_name = call.get("name", "")
                        tool_args = call.get("arguments", {})
                        observation = await self.execute_tool(tool_name, **tool_args)
                        messages.append(
                            {
                                "role": "assistant",
                                "content": text,
                                "tool_calls": [call],
                            }
                        )
                        messages.append(
                            {
                                "role": "tool",
                                "content": str(observation),
                            }
                        )
                else:
                    return text
            except Exception as e:
                logger.error("LLM execution failed: %s", e)
                return f"Execution failed: {e}"

        return "Task completed with maximum iterations"

    async def _execute_direct(self, task: str, context: dict | None = None) -> str:
        """Execute task using LLM for real reasoning (with keyword fallback)."""
        try:
            from backend.app.services.llm.manager import llm_manager
            from backend.app.services.llm.provider import LLMMessage

            system_prompt = self._build_system_prompt(context)
            messages = [
                LLMMessage(role="system", content=system_prompt),
                LLMMessage(role="user", content=task),
            ]
            model_id = getattr(self._agent, "model_id", None) if self._agent else None
            response = await llm_manager.chat(messages, model=model_id, max_tokens=2048, temperature=0.3)
            return response.content
        except (RuntimeError, Exception):
            # No LLM available, fall back to keyword routing
            return await self._keyword_fallback(task)

    def _build_system_prompt(self, context: dict | None = None) -> str:
        """Build system prompt with optional context."""
        prompt = EXECUTOR_SYSTEM_PROMPT
        if context:
            prompt += f"\n\nContext:\n{context}"
        return prompt

    async def _keyword_fallback(self, task: str) -> str:
        """Fallback keyword-based routing when no LLM is available."""
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

        return (
            f"Task received: {task}\n\n"
            "I can help with:\n"
            "- Searching code (try: 'search for authentication functions')\n"
            "- Reading files (try: 'read backend/app/main.py')\n"
            "- Listing files (try: 'list files in backend/app/')\n"
        )

    def _extract_search_query(self, task: str) -> str:
        """Extract search query from task text."""
        # Simple extraction: take everything after common prefixes
        for prefix in ["search for", "find", "look for", "search", "find"]:
            if prefix in task.lower():
                idx = task.lower().index(prefix)
                return task[idx + len(prefix) :].strip().strip("\"'")
        return task.strip()

    def _extract_path(self, task: str) -> str | None:
        """Extract a file path from task text."""
        import re

        # Look for path-like patterns
        match = re.search(r"[\w/.\-]+\.\w+", task)
        return match.group(0) if match else None

    async def _search_tool(self, query: str) -> str:
        """Search across code and memories."""
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
        """Read a file's contents."""
        try:
            from backend.app.agents.tool_defs import _ensure_within_workspace

            target = _ensure_within_workspace(path)
            if not target.exists():
                return f"File not found: {path}"
            content = target.read_text(encoding="utf-8", errors="replace")
            # Truncate large files
            if len(content) > 10000:
                content = content[:10000] + f"\n... (truncated, {len(content)} total chars)"
            return content
        except ValueError as e:
            return str(e)
        except Exception as e:
            return f"Error reading {path}: {e}"

    async def _write_file_tool(self, path: str, content: str = "") -> str:
        """Write content to a file."""
        try:
            from backend.app.agents.tool_defs import _ensure_within_workspace

            target = _ensure_within_workspace(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return f"Written {len(content)} chars to {path}"
        except ValueError as e:
            return str(e)
        except Exception as e:
            return f"Error writing {path}: {e}"

    async def _list_files_tool(self, path: str = ".") -> str:
        """List files in a directory."""
        try:
            from backend.app.agents.tool_defs import _ensure_within_workspace

            dir_path = _ensure_within_workspace(path)
            if not dir_path.is_dir():
                return f"Not a directory: {path}"
            entries = sorted(dir_path.iterdir(), key=lambda p: (not p.is_dir(), p.name))
            lines = []
            for entry in entries[:50]:
                prefix = "  " if entry.is_dir() else "  "
                suffix = "/" if entry.is_dir() else ""
                lines.append(f"{prefix}{entry.name}{suffix}")
            if len(list(dir_path.iterdir())) > 50:
                lines.append(f"  ... and {len(list(dir_path.iterdir())) - 50} more")
            return "\n".join(lines) if lines else "Empty directory"
        except Exception as e:
            return f"Error listing {path}: {e}"
