from typing import Dict, List

from backend.app.tools.base import BaseTool, ToolContext
from backend.app.tools.builtins import FileSearchTool, RagTool, SystemScannerTool


class ToolRegistry:
    """
    SINGLE RESPONSIBILITY:
    - store tools
    - expose tools to executor
    """

    def __init__(self, executor=None):
        self.executor = executor
        self.tools: Dict[str, BaseTool] = {}

        if executor is not None:
            self.register(FileSearchTool(executor))
            self.register(SystemScannerTool(executor))
            self.register(RagTool(executor))

    def register(self, tool: BaseTool):
        self.tools[tool.name] = tool

    def get(self, name: str):
        return self.tools.get(name)

    def list_tools(self) -> List[str]:
        return list(self.tools.keys())

    def all(self) -> List[BaseTool]:
        return list(self.tools.values())

    async def execute(
        self,
        name: str,
        context: ToolContext,
    ):
        tool = self.get(name)

        if tool is None:
            return None

        decision = tool.decide(context)

        if not decision.get("should_run", False):
            return {
                "tool": name,
                "skipped": True,
                "reason": decision.get("reason", "no reason"),
            }

        result = await tool.run(context, decision.get("params", {}))

        return {
            "tool": name,
            "output": result,
            "reflection": tool.reflect(result),
        }
