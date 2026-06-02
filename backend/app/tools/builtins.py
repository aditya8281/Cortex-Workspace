from backend.app.tools.base import RegisteredTool, ToolContext
from backend.app.tools.base import ToolResult
from backend.app.tools.metadata import ToolMetadata


# -------------------------------------------------
# FILE SEARCH TOOL
# -------------------------------------------------
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
            "reason": "file search requested",
            "params": {},
        }

    async def run(self, context: ToolContext, params):

        try:
            result = self.executor.file_agent.search(context.query)

            return {
                "query": context.query,
                "results": result,
                "count": len(result) if result else 0
            }

        except Exception as e:

            return {
                "error": str(e),
                "query": context.query
            }


# -------------------------------------------------
# SYSTEM SCANNER TOOL
# -------------------------------------------------
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

        try:
            result = self.executor.system_agent.scan()

            return {
                "status": "ok",
                "diagnostics": result
            }

        except Exception as e:

            return {
                "status": "error",
                "error": str(e)
            }


# -------------------------------------------------
# RAG TOOL
# -------------------------------------------------
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
            "reason": "repository retrieval requested",
            "params": {},
        }

    async def run(self, context: ToolContext, params):

        try:
            results = self.executor.rag.search(context.query)

            if not results:
                return {
                    "query": context.query,
                    "chunks": [],
                    "count": 0
                }

            chunks = []

            for item in results:
                try:
                    chunks.append(item["data"]["chunk"][:500])
                except Exception:
                    continue

            return {
                "query": context.query,
                "chunks": chunks,
                "count": len(chunks)
            }

        except Exception as e:

            return {
                "error": str(e),
                "query": context.query
            }