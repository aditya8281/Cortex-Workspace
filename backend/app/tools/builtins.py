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

        results = self.executor.rag.search(
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
