from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Literal
from dataclasses import dataclass


# -------------------------------------------------
# TOOL CONTEXT (SAFE + STRUCTURED)
# -------------------------------------------------
@dataclass
class ToolContext:
    user_id: Optional[int] = None
    query: str = ""
    state: Dict[str, Any] = None


# -------------------------------------------------
# STANDARDIZED TOOL RESULT (CRITICAL FIX)
# -------------------------------------------------
@dataclass
class ToolResult:
    tool: str
    status: Literal["success", "skipped", "error"]
    output: Any = None
    reason: Optional[str] = None
    meta: Dict[str, Any] = None


# -------------------------------------------------
# BASE TOOL
# -------------------------------------------------
class BaseTool(ABC):

    name: str

    # -------------------------------------------------
    # DECISION LAYER (MUST BE STRICT)
    # -------------------------------------------------
    @abstractmethod
    def decide(self, context: ToolContext) -> Dict[str, Any]:
        """
        Must return:
        {
            "should_run": bool,
            "reason": str,
            "params": dict
        }
        """
        pass

    # -------------------------------------------------
    # EXECUTION LAYER
    # -------------------------------------------------
    @abstractmethod
    async def run(self, context: ToolContext, params: Dict[str, Any]) -> Any:
        pass

    # -------------------------------------------------
    # STANDARDIZED REFLECTION
    # -------------------------------------------------
    def reflect(self, result: Any) -> Dict[str, Any]:
        return {
            "tool": self.name,
            "success": result is not None,
            "type": type(result).__name__
        }

    # -------------------------------------------------
    # SAFE WRAPPER (IMPORTANT ADDITION)
    # -------------------------------------------------
    async def execute(self, context: ToolContext) -> ToolResult:

        decision = self.decide(context)

        if not decision.get("should_run", True):
            return ToolResult(
                tool=self.name,
                status="skipped",
                reason=decision.get("reason", "no reason"),
                output=None
            )

        try:
            result = await self.run(context, decision.get("params", {}))

            return ToolResult(
                tool=self.name,
                status="success",
                output=result,
                meta=self.reflect(result)
            )

        except Exception as e:

            return ToolResult(
                tool=self.name,
                status="error",
                output=None,
                reason=str(e)
            )


# -------------------------------------------------
# REGISTERED TOOL (UNCHANGED BUT NOW COMPATIBLE)
# -------------------------------------------------
class RegisteredTool(BaseTool):

    metadata: Any  # keep flexible unless you want strict schema

    def get_metadata(self):
        return self.metadata