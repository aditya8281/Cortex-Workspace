from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass, field

from backend.app.tools.metadata import ToolMetadata


# -------------------------------------------------
# STANDARD TOOL OUTPUT CONTRACT (NEW CORE LAYER)
# -------------------------------------------------
@dataclass
class ToolResult:
    tool: str
    output: Any

    status: str = "success"  # success | error | skipped
    skipped: bool = False
    reason: Optional[str] = None

    confidence: float = 1.0
    relevance: float = 1.0

    meta: Dict[str, Any] = field(default_factory=dict)


# -------------------------------------------------
# TOOL CONTEXT
# -------------------------------------------------
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
# BASE TOOL CONTRACT
# -------------------------------------------------
class BaseTool(ABC):
    name: str

    @abstractmethod
    def decide(self, context: ToolContext) -> Dict[str, Any]:
        """
        Returns:
        {
            should_run: bool,
            reason: str,
            params: dict,
            confidence?: float
        }
        """
        pass

    @abstractmethod
    async def run(self, context: ToolContext, params: Dict[str, Any]) -> Any:
        pass

    def reflect(self, result: Any) -> Dict[str, Any]:
        return {
            "tool": self.name,
            "success": result is not None
        }


# -------------------------------------------------
# REGISTERED TOOL (keeps metadata system intact)
# -------------------------------------------------
class RegisteredTool(BaseTool):
    metadata: ToolMetadata

    def get_metadata(self) -> ToolMetadata:
        return self.metadata