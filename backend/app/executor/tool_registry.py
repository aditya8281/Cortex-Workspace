from typing import Dict, List, Optional

from backend.app.tools.base import BaseTool, ToolContext, ToolResult
from backend.app.tools.builtins import (
    FileSearchTool,
    RagTool,
    SystemActionsTool,
    SystemScannerTool,
)


class ToolRegistry:
    def __init__(self, executor=None):
        self.executor = executor
        self.tools: Dict[str, BaseTool] = {}

        if executor is not None:
            self.register(FileSearchTool(executor))
            self.register(SystemScannerTool(executor))
            self.register(RagTool(executor))
            self.register(SystemActionsTool(executor))

    def register(self, tool: BaseTool):
        self.tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        return self.tools.get(name)

    def list_tools(self) -> List[str]:
        return list(self.tools.keys())

    def all(self) -> List[BaseTool]:
        return list(self.tools.values())

    async def execute(
        self,
        name: str,
        context: ToolContext,
    ) -> ToolResult:

        tool = self.get(name)

        if tool is None:
            return ToolResult(
                tool=name,
                status="error",
                output=None,
                reason="tool_not_found"
            )

        return await tool.execute(context)
