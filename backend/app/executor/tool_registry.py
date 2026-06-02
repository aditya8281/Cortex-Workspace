from typing import Callable, Any


class ToolRegistry:

    def __init__(self, executor):
        self.executor = executor

        self.tools: dict[str, Callable] = {
            "file_search": self._file_search,
            "system_scanner": self._system_scanner,
            "rag": self._rag
        }

    # -------------------------------------------------
    # PUBLIC EXECUTOR
    # -------------------------------------------------
    async def execute(self, tool_name: str, query: str) -> Any:

        tool = self.tools.get(tool_name)

        if not tool:
            return f"Unknown tool: {tool_name}"

        return await tool(query)

    # -------------------------------------------------
    # TOOL WRAPPERS
    # -------------------------------------------------
    async def _file_search(self, query: str):
        return self.executor.file_agent.search(query)

    async def _system_scanner(self, query: str):
        return self.executor.system_agent.scan(query)

    async def _rag(self, query: str):

        results = self.executor.rag.search(query)

        if not results:
            return None

        return "\n\n".join(
            item["data"]["chunk"][:500]
            for item in results
        )