from dataclasses import dataclass, field
from typing import Any, Dict, List

from backend.app.tools.base import ToolResult


# -------------------------------------------------
# MEMORY ITEM
# -------------------------------------------------
@dataclass
class MemoryItem:
    content: str
    score: float = 0.0
    source: str = "memory"


# -------------------------------------------------
# EXECUTION CONTEXT
# -------------------------------------------------
@dataclass
class ExecutionContext:
    query: str

    user_id: int | None = None

    # NEW
    execution_id: str | None = None

    memory: Any = None

    tool_results: List[ToolResult] = field(default_factory=list)

    llm_response: str | None = None

    routing_info: Any = None

    meta: Dict[str, Any] = field(default_factory=dict)