from typing import Dict, List, Optional

from backend.app.tools.base import BaseTool, ToolContext, ToolResult
from backend.app.tools.builtins import FileSearchTool, RagTool, SystemScannerTool


class ToolRegistry:
    """
    SINGLE RESPONSIBILITY:
    - store tools
    - provide unified execution access
    """

    def __init__(self, executor=None):
        self.executor = executor
        self.tools: Dict[str, BaseTool] = {}

        if executor is not None:
            self.register(FileSearchTool(executor))
            self.register(SystemScannerTool(executor))
            self.register(RagTool(executor))

    # -------------------------------------------------
    # REGISTRATION
    # -------------------------------------------------
    def register(self, tool: BaseTool):
        self.tools[tool.name] = tool

    # -------------------------------------------------
    # LOOKUP
    # -------------------------------------------------
    def get(self, name: str) -> Optional[BaseTool]:
        return self.tools.get(name)

    def list_tools(self) -> List[str]:
        return list(self.tools.keys())

    def all(self) -> List[BaseTool]:
        return list(self.tools.values())

    # -------------------------------------------------
    # SINGLE EXECUTION AUTHORITY (IMPORTANT FIX)
    # -------------------------------------------------
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

        # DELEGATE TO BASE TOOL EXECUTION PIPELINE
        return await tool.execute(context)