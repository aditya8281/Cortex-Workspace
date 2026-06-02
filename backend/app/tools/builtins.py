from backend.app.tools.base import RegisteredTool, ToolContext
from backend.app.tools.metadata import ToolMetadata


class FileSearchTool(RegisteredTool):
    name = "file_search"

    def __init__(self, executor):
        self.executor = executor
        self.metadata = ToolMetadata(
            name=self.name,
            description="Search workspace files and file contents.",
            capabilities=["file_search", "workspace_scan"],
            priority=10,
            tags=["files", "search"],
        )

    def decide(self, context: ToolContext):
        query = context.query.strip()

        if not query:
            return {
                "should_run": False,
                "reason": "empty query",
                "params": {},
            }

        return {
            "should_run": True,
            "reason": "workspace search requested",
            "params": {},
        }

    async def run(self, context: ToolContext, params):
        return self.executor.file_agent.search(context.query)


class SystemScannerTool(RegisteredTool):
    name = "system_scanner"

    def __init__(self, executor):
        self.executor = executor
        self.metadata = ToolMetadata(
            name=self.name,
            description="Inspect system health and workspace diagnostics.",
            capabilities=["system_scan", "diagnostics"],
            priority=8,
            tags=["system", "health"],
        )

    def decide(self, context: ToolContext):
        return {
            "should_run": True,
            "reason": "system diagnostics requested",
            "params": {},
        }

    async def run(self, context: ToolContext, params):
        return self.executor.system_agent.scan(context.query)


class RagTool(RegisteredTool):
    name = "rag"

    def __init__(self, executor):
        self.executor = executor
        self.metadata = ToolMetadata(
            name=self.name,
            description="Retrieve repository context from the codebase index.",
            capabilities=["rag", "repository_search"],
            priority=9,
            tags=["code", "retrieval"],
        )

    def decide(self, context: ToolContext):
        return {
            "should_run": True,
            "reason": "repository context requested",
            "params": {},
        }

    async def run(self, context: ToolContext, params):
        results = self.executor.rag.search(context.query)

        if not results:
            return None

        return "\n\n".join(
            item["data"]["chunk"][:500]
            for item in results
        )
