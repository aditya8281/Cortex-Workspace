from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class ToolContext:
    """
    Shared context passed to every tool.
    """
    def __init__(
        self,
        user_id: Optional[int] = None,
        query: str = "",
        state: Optional[Dict[str, Any]] = None
    ):
        self.user_id = user_id
        self.query = query
        self.state = state or {}


class BaseTool(ABC):
    """
    Autonomous Tool Unit (ATU)

    Every tool now has:
    - decide(): should it run + how
    - run(): actual execution
    """

    name: str

    @abstractmethod
    def decide(self, context: ToolContext) -> Dict[str, Any]:
        """
        Tool "brain".
        Returns:
        {
            "should_run": bool,
            "reason": str,
            "params": dict
        }
        """
        pass

    @abstractmethod
    async def run(self, context: ToolContext, params: Dict[str, Any]) -> Any:
        """
        Executes tool logic.
        """
        pass

    def reflect(self, result: Any) -> Dict[str, Any]:
        """
        Optional self-evaluation layer (MVP simple).
        """
        return {
            "tool": self.name,
            "success": result is not None
        }