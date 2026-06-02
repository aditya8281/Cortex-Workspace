from typing import Dict, Any, List
from backend.app.tools.base import BaseTool, ToolContext


class ToolRegistry:
    """
    Now acts as TOOL ORCHESTRATOR, not just function map.
    """

    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        self.tools[tool.name] = tool

    def list_tools(self) -> List[str]:
        return list(self.tools.keys())

    async def execute_auto(self, query: str, user_id: int = None) -> Dict[str, Any]:
        """
        AUTONOMOUS MODE:
        - tools decide themselves if they should run
        """

        context = ToolContext(user_id=user_id, query=query)

        results = []

        for tool in self.tools.values():
            decision = tool.decide(context)

            if decision.get("should_run"):
                output = await tool.run(context, decision.get("params", {}))

                results.append({
                    "tool": tool.name,
                    "output": output,
                    "reflection": tool.reflect(output),
                    "reason": decision.get("reason")
                })

        return {
            "query": query,
            "results": results
        }