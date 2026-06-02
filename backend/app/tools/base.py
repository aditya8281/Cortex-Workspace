from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


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


# -------------------------------------------------
# FINAL TOOL RESULT (RUNTIME OBJECT)
# -------------------------------------------------
class ToolResult:
    def __init__(
        self,
        tool: str,
        output: Any = None,
        confidence: float = 1.0,
        relevance: float = 1.0,
        status: str = "success",
        meta: Optional[Dict[str, Any]] = None
    ):
        self.tool = tool
        self.output = output
        self.confidence = confidence
        self.relevance = relevance
        self.status = status
        self.meta = meta or {}

    def to_dict(self):
        return {
            "tool": self.tool,
            "output": self.output,
            "confidence": self.confidence,
            "relevance": self.relevance,
            "status": self.status,
            "meta": self.meta,
        }


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
            "success": result is not None,
            "status": getattr(result, "status", None)
        }


class RegisteredTool(BaseTool):
    metadata = None