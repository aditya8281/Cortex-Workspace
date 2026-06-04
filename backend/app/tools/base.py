from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class ToolContext:
    def __init__(
        self,
        user_id: Optional[int] = None,
        query: str = "",
        state: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ):
        self.user_id = user_id
        self.query = query
        self.state = state or {}
        self.params = params or {}


class ToolResult:
    def __init__(
        self,
        tool: str,
        output: Any = None,
        confidence: float = 1.0,
        relevance: float = 1.0,
        status: str = "success",
        skipped: bool = False,
        reason: str | None = None,
        meta: Optional[Dict[str, Any]] = None
    ):
        self.tool = tool
        self.output = output
        self.confidence = confidence
        self.relevance = relevance
        self.status = status
        self.skipped = skipped
        self.reason = reason
        self.meta = meta or {}

    def to_dict(self):
        return {
            "tool": self.tool,
            "output": self.output,
            "confidence": self.confidence,
            "relevance": self.relevance,
            "status": self.status,
            "skipped": self.skipped,
            "reason": self.reason,
            "meta": self.meta,
        }

    def __str__(self) -> str:
        if self.status == "error":
            error_msg = (self.meta or {}).get("error") or (self.meta or {}).get("reason") or "Unknown error"
            return f"[Tool Error — {self.tool}]: {error_msg}"
        if self.status == "skipped":
            return f"[Skipped — {self.tool}]: {self.reason or 'Not applicable'}"
        if self.output is not None:
            return str(self.output)
        return f"[{self.tool}]"

    def __repr__(self) -> str:
        return f"ToolResult(tool={self.tool!r}, status={self.status!r}, output={str(self.output)[:60]!r})"


class BaseTool(ABC):

    name: str
    aliases: list[str] = []
    permission_level: str = "standard"
    input_schema: Dict[str, Any] = {"type": "object", "additionalProperties": True}
    output_schema: Dict[str, Any] = {"type": "object", "additionalProperties": True}

    @abstractmethod
    def decide(self, context: ToolContext) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def run(self, context: ToolContext, params: Dict[str, Any]) -> ToolResult:
        pass

    async def execute(self, context: ToolContext) -> ToolResult:
        params = dict(getattr(context, "params", {}) or {})
        force_run = bool(params.pop("__force__", False))

        if force_run:
            result = await self.run(context, params)
            if isinstance(result, ToolResult):
                return result

            return ToolResult(
                tool=self.name,
                output=result,
                confidence=1.0,
                relevance=1.0,
                status="success",
                skipped=False,
                meta={
                    "params": params,
                    "reflection": self.reflect(result),
                }
            )

        decision = self.decide(context)
        merged_params = {**decision.get("params", {}), **params}

        if not decision.get("should_run", False):
            return ToolResult(
                tool=self.name,
                output=None,
                confidence=1.0,
                relevance=0.0,
                status="skipped",
                skipped=True,
                reason=decision.get("reason", "skipped"),
                meta={"params": merged_params}
            )

        result = await self.run(context, merged_params)

        if isinstance(result, ToolResult):
            return result

        return ToolResult(
            tool=self.name,
            output=result,
            confidence=decision.get("confidence", 1.0),
            relevance=decision.get("relevance", 1.0),
            status="success",
            skipped=False,
            meta={
                "params": merged_params,
                "reflection": self.reflect(result),
            }
        )

    def spec(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "aliases": list(getattr(self, "aliases", []) or []),
            "input_schema": getattr(self, "input_schema", {"type": "object"}),
            "output_schema": getattr(self, "output_schema", {"type": "object"}),
            "permission_level": getattr(self, "permission_level", "standard"),
        }

    def reflect(self, result: ToolResult) -> Dict[str, Any]:
        status = getattr(result, "status", None) if isinstance(result, ToolResult) else None

        if status is None and result is not None:
            status = "success"

        return {
            "tool": self.name,
            "success": result is not None,
            "status": status
        }


class RegisteredTool(BaseTool):
    metadata = None
