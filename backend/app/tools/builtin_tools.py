import asyncio
import shlex
from pathlib import Path

from backend.app.core.config import settings
from backend.app.tools.base import RegisteredTool, ToolContext, ToolResult


class FileSearchTool(RegisteredTool):
    name = "file_search"
    aliases = ["search_files"]
    input_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
        },
        "required": ["query"],
        "additionalProperties": True,
    }
    output_schema = {
        "type": "object",
        "properties": {
            "result": {"type": "string"},
            "count": {"type": "integer"},
        },
        "required": ["result", "count"],
        "additionalProperties": True,
    }

    def __init__(self, executor):
        self.executor = executor

    def decide(self, context: ToolContext):

        if not context.query.strip():
            return {"should_run": False, "reason": "empty", "params": {}}

        return {"should_run": True, "reason": "search", "params": {}}

    async def run(self, context: ToolContext, params):

        result = self.executor.file_agent.search(context.query)
        matches = []
        for line in str(result).splitlines():
            cleaned = line.strip()
            if cleaned.startswith("- "):
                path = cleaned[2:].replace("[File] ", "").replace("[Content Match] ", "")
                matches.append({
                    "line": cleaned,
                    "path": path,
                })

        return {
            "result": result,
            "count": len(matches),
            "primary_path": matches[0]["path"] if matches else None,
            "matches": matches,
        }


class SearchFilesTool(FileSearchTool):
    name = "search_files"
    aliases = ["file_search"]


class SystemScannerTool(RegisteredTool):
    name = "system_scanner"
    aliases = ["system_scan"]
    input_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
        },
        "additionalProperties": True,
    }
    output_schema = {
        "type": "object",
        "properties": {
            "diagnostics": {"type": "string"},
        },
        "required": ["diagnostics"],
        "additionalProperties": True,
    }

    def __init__(self, executor):
        self.executor = executor

    def decide(self, context: ToolContext):
        return {"should_run": True, "reason": "system", "params": {}}

    async def run(self, context: ToolContext, params):

        result = self.executor.system_agent.scan(context.query)

        return {
            "diagnostics": result
        }


class SystemActionsTool(RegisteredTool):
    name = "system_actions"
    permission_level = "restricted"

    def __init__(self, executor):
        self.executor = executor

    def decide(self, context: ToolContext):
        query = context.query.lower()
        triggers = (
            "open file",
            "open folder",
            "launch",
            "run command",
            "execute",
            "read file",
            "list directory",
        )
        if any(t in query for t in triggers):
            return {"should_run": True, "reason": "system_action", "params": {}}
        return {"should_run": False, "reason": "no_action_intent", "params": {}}

    async def run(self, context: ToolContext, params):
        from backend.app.db.session import SessionLocal
        from backend.app.intelligence.system_actions import SystemActionsService

        query = context.query.lower()
        service = SystemActionsService()
        db = SessionLocal()
        try:
            if "open folder" in query:
                return await self._plan(
                    service, db, context, "open_folder", "Open folder requested from chat", [],
                )
            if "read file" in query:
                return await self._plan(
                    service, db, context, "read_file", "Read file requested from chat", [],
                )
            if "run command" in query or "execute" in query:
                return await self._plan(
                    service, db, context, "run_command", "Terminal command requested from chat",
                    [], {"command": context.query, "category": "terminal"},
                )
            return {
                "available_actions": [
                    "open_file", "open_folder", "read_file",
                    "list_directory", "run_command", "search_files",
                ],
                "note": "Use the intelligence API to plan actions with affected paths.",
            }
        finally:
            db.close()

    async def _plan(self, service, db, context: ToolContext, action_type: str,
                    description: str, paths: list, payload: dict | None = None):
        result = service.plan_action(
            db, user_id=context.user_id, action_type=action_type,
            description=description, affected_paths=paths,
            payload=payload or {}, category=(payload or {}).get("category"),
        )
        return result


class ReadFileTool(RegisteredTool):
    name = "read_file"
    aliases = []
    input_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "max_bytes": {"type": "integer"},
        },
        "required": ["path"],
        "additionalProperties": True,
    }
    output_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"},
            "cached": {"type": "boolean"},
        },
        "required": ["path", "content"],
        "additionalProperties": True,
    }

    def __init__(self, executor):
        self.executor = executor

    def decide(self, context: ToolContext):
        params = context.params or {}
        if params.get("path"):
            return {"should_run": True, "reason": "workflow_read", "params": params}
        return {"should_run": False, "reason": "missing_path", "params": params}

    async def run(self, context: ToolContext, params):
        path_value = params.get("path")
        if not path_value:
            return ToolResult(tool=self.name, output=None, status="error", meta={"error": "missing_path"})

        path = Path(path_value).expanduser().resolve()
        workspace_root = Path(settings.WORKSPACE_ROOT).resolve()
        if workspace_root not in path.parents and path != workspace_root:
            return ToolResult(tool=self.name, output=None, status="error", meta={"error": "path_outside_workspace"})

        file_cache = context.state.setdefault("file_cache", {})
        cache_key = str(path)
        if cache_key in file_cache:
            return {"path": cache_key, "content": file_cache[cache_key], "cached": True}

        max_bytes = int(params.get("max_bytes") or 200_000)
        content = path.read_text(encoding="utf-8", errors="ignore")[:max_bytes]
        file_cache[cache_key] = content
        context.state.setdefault("retrieved_context", {})[cache_key] = content[:5000]
        context.state.setdefault("intermediate_outputs", {})[context.query or cache_key] = content[:1000]
        context.state.setdefault("retrieved_files", []).append(cache_key)

        return {"path": cache_key, "content": content, "cached": False}


class WriteFileTool(RegisteredTool):
    name = "write_file"
    aliases = []
    permission_level = "restricted"
    input_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"},
            "overwrite": {"type": "boolean"},
        },
        "required": ["path", "content"],
        "additionalProperties": True,
    }
    output_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "written": {"type": "boolean"},
        },
        "required": ["path", "written"],
        "additionalProperties": True,
    }

    def __init__(self, executor):
        self.executor = executor

    def decide(self, context: ToolContext):
        params = context.params or {}
        if params.get("path") and params.get("content"):
            return {"should_run": True, "reason": "workflow_write", "params": params}
        return {"should_run": False, "reason": "missing_write_args", "params": params}

    async def run(self, context: ToolContext, params):
        permissions = (context.state or {}).get("permissions", {})
        if not permissions.get("write_file"):
            return ToolResult(tool=self.name, output=None, status="error", meta={"error": "permission_denied"})

        path = Path(params["path"]).expanduser().resolve()
        workspace_root = Path(settings.WORKSPACE_ROOT).resolve()
        if workspace_root not in path.parents and path != workspace_root:
            return ToolResult(tool=self.name, output=None, status="error", meta={"error": "path_outside_workspace"})

        overwrite = bool(params.get("overwrite", True))
        if path.exists() and not overwrite:
            return ToolResult(tool=self.name, output=None, status="error", meta={"error": "file_exists"})

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(params["content"], encoding="utf-8")
        context.state.setdefault("intermediate_outputs", {})[str(path)] = params["content"][:1000]
        return {"path": str(path), "written": True}


class MemorySearchTool(RegisteredTool):
    name = "memory_search"
    aliases = []
    input_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
        },
        "required": ["query"],
        "additionalProperties": True,
    }
    output_schema = {
        "type": "object",
        "properties": {
            "matches": {"type": "array"},
            "count": {"type": "integer"},
        },
        "required": ["matches", "count"],
        "additionalProperties": True,
    }

    def __init__(self, executor):
        self.executor = executor

    def decide(self, context: ToolContext):
        params = context.params or {}
        if params.get("query"):
            return {"should_run": True, "reason": "workflow_memory", "params": params}
        return {"should_run": False, "reason": "missing_query", "params": params}

    async def run(self, context: ToolContext, params):
        query = params.get("query") or context.query
        user_id = context.user_id
        matches = []

        if user_id is not None:
            try:
                matches = self.executor.memory.search(user_id=user_id, query=query) or []
            except Exception as exc:
                return ToolResult(tool=self.name, output=None, status="error", meta={"error": str(exc)})

        if isinstance(matches, str):
            matches = [{"content": matches}]

        return {"matches": matches, "count": len(matches)}


class TerminalExecuteTool(RegisteredTool):
    name = "terminal_execute"
    permission_level = "restricted"
    input_schema = {
        "type": "object",
        "properties": {
            "command": {"type": "string"},
            "cwd": {"type": "string"},
            "timeout": {"type": "integer"},
        },
        "required": ["command"],
        "additionalProperties": True,
    }
    output_schema = {
        "type": "object",
        "properties": {
            "returncode": {"type": "integer"},
            "stdout": {"type": "string"},
            "stderr": {"type": "string"},
        },
        "required": ["returncode", "stdout", "stderr"],
        "additionalProperties": True,
    }

    def __init__(self, executor):
        self.executor = executor

    def decide(self, context: ToolContext):
        params = context.params or {}
        if params.get("command"):
            return {"should_run": True, "reason": "workflow_terminal", "params": params}
        return {"should_run": False, "reason": "missing_command", "params": params}

    async def run(self, context: ToolContext, params):
        permissions = (context.state or {}).get("permissions", {})
        if not permissions.get("terminal_execute"):
            return ToolResult(tool=self.name, output=None, status="error", meta={"error": "permission_denied"})

        command = params["command"]
        cwd = Path(params.get("cwd") or settings.WORKSPACE_ROOT).expanduser().resolve()
        workspace_root = Path(settings.WORKSPACE_ROOT).resolve()
        if workspace_root not in cwd.parents and cwd != workspace_root:
            return ToolResult(tool=self.name, output=None, status="error", meta={"error": "cwd_outside_workspace"})

        timeout = int(params.get("timeout") or 30)
        proc = await asyncio.create_subprocess_exec(
            *shlex.split(command),
            cwd=str(cwd),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            return ToolResult(tool=self.name, output=None, status="error", meta={"error": "timeout"})

        return {
            "returncode": proc.returncode,
            "stdout": stdout.decode("utf-8", errors="ignore"),
            "stderr": stderr.decode("utf-8", errors="ignore"),
        }
