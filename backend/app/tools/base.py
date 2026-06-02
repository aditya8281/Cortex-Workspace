from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypedDict


class ToolContext:
    def __init__(
        self,
        user_id: Optional[int] = None,
        query: str = "",
        state: Optional[Dict[str, Any]] = None
    ):
        self.user_id = user_id
        self.query = query
        self.state = state or {}


# ✅ NEW STANDARD TOOL OUTPUT FORMAT
class ToolResult(TypedDict):
    tool: str
    output: Any
    confidence: float
    relevance: float
    meta: Dict[str, Any]


class BaseTool(ABC):

    name: str

    @abstractmethod
    def decide(self, context: ToolContext) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def run(self, context: ToolContext, params: Dict[str, Any]) -> ToolResult:
        pass

    def reflect(self, result: ToolResult) -> Dict[str, Any]:
        return {
            "tool": self.name,
            "success": result is not None
        }


class RegisteredTool(BaseTool):
    metadata = None