from typing import Dict, List, Optional

from backend.app.tools.base import BaseTool, ToolContext, ToolResult
from backend.app.tools.builtin_tools import (
    MemorySearchTool,
    RagRetrieveTool,
    FileSearchTool,
    ReadFileTool,
    SearchFilesTool,
    RagTool,
    TerminalExecuteTool,
    SystemActionsTool,
    SystemScannerTool,
    WriteFileTool,
)


class ToolRegistry:
    def __init__(self, executor=None):
        self.executor = executor
        self.tools: Dict[str, BaseTool] = {}
        self.aliases: Dict[str, str] = {}

        if executor is not None:
            self.register(FileSearchTool(executor))
            self.register(SearchFilesTool(executor))
            self.register(ReadFileTool(executor))
            self.register(WriteFileTool(executor))
            self.register(MemorySearchTool(executor))
            self.register(SystemScannerTool(executor))
            self.register(RagTool(executor))
            self.register(RagRetrieveTool(executor))
            self.register(SystemActionsTool(executor))
            self.register(TerminalExecuteTool(executor))

    def register(self, tool: BaseTool):
        self.tools[tool.name] = tool
        for alias in getattr(tool, "aliases", []) or []:
            self.aliases[alias] = tool.name

    def get(self, name: str) -> Optional[BaseTool]:
        resolved = self.resolve_name(name)
        return self.tools.get(resolved)

    def resolve_name(self, name: str) -> str:
        if name in self.tools:
            return name
        return self.aliases.get(name, name)

    def list_tools(self) -> List[str]:
        return list(self.tools.keys())

    def all(self) -> List[BaseTool]:
        return list(self.tools.values())

    def spec(self, name: str) -> dict | None:
        tool = self.get(name)
        return tool.spec() if tool else None

    def available_specs(self) -> list[dict]:
        return [tool.spec() for tool in self.tools.values()]

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
