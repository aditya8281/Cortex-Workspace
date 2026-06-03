from backend.app.tools.base import RegisteredTool, ToolContext


class FileSearchTool(RegisteredTool):
    name = "file_search"

    def __init__(self, executor):
        self.executor = executor

    def decide(self, context: ToolContext):

        if not context.query.strip():
            return {"should_run": False, "reason": "empty", "params": {}}

        return {"should_run": True, "reason": "search", "params": {}}

    async def run(self, context: ToolContext, params):

        result = self.executor.file_agent.search(context.query)

        return {
            "result": result,
            "count": len(result) if result else 0
        }


class SystemScannerTool(RegisteredTool):
    name = "system_scanner"

    def __init__(self, executor):
        self.executor = executor

    def decide(self, context: ToolContext):
        return {"should_run": True, "reason": "system", "params": {}}

    async def run(self, context: ToolContext, params):

        result = self.executor.system_agent.scan(context.query)

        return {
            "diagnostics": result
        }


class RagTool(RegisteredTool):
    name = "rag"

    def __init__(self, executor):
        self.executor = executor

    def decide(self, context: ToolContext):
        return {"should_run": True, "reason": "rag", "params": {}}

    async def run(self, context: ToolContext, params):
        state = context.state or {}
        embedding_model = state.get("embedding_model")
        vector_db = state.get("vector_db")
        code_parsing = state.get("code_parsing")

        results = await self.executor.rag.search(
            context.query,
            embedding_model=embedding_model,
            vector_db=vector_db,
            code_parsing=code_parsing
        )

        if not results:
            return {"chunks": [], "count": 0}

        chunks = [
            item["data"]["chunk"][:500]
            for item in results
        ]

        return {
            "chunks": chunks,
            "count": len(chunks)
        }


class SystemActionsTool(RegisteredTool):
    name = "system_actions"

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
                    service,
                    db,
                    context,
                    "open_folder",
                    "Open folder requested from chat",
                    [],
                )
            if "read file" in query:
                return await self._plan(
                    service,
                    db,
                    context,
                    "read_file",
                    "Read file requested from chat",
                    [],
                )
            if "run command" in query or "execute" in query:
                return await self._plan(
                    service,
                    db,
                    context,
                    "run_command",
                    "Terminal command requested from chat",
                    [],
                    {"command": context.query, "category": "terminal"},
                )
            return {
                "available_actions": [
                    "open_file",
                    "open_folder",
                    "read_file",
                    "list_directory",
                    "run_command",
                    "search_files",
                ],
                "note": "Use the intelligence API to plan actions with affected paths.",
            }
        finally:
            db.close()

    async def _plan(
        self,
        service,
        db,
        context: ToolContext,
        action_type: str,
        description: str,
        paths: list,
        payload: dict | None = None,
    ):
        result = service.plan_action(
            db,
            user_id=context.user_id,
            action_type=action_type,
            description=description,
            affected_paths=paths,
            payload=payload or {},
            category=(payload or {}).get("category"),
        )
        return result
