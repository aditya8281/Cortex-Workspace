from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# -------------------------------------------------
# TOOL RESULT (NOW WITH INTELLIGENCE SIGNALS)
# -------------------------------------------------
@dataclass
class ToolResult:
    tool: str
    output: Any

    status: str = "success"
    skipped: bool = False
    reason: Optional[str] = None

    # NEW: intelligence signals
    confidence: float = 1.0
    relevance: float = 1.0

    meta: Dict[str, Any] = field(default_factory=dict)


# -------------------------------------------------
# MEMORY ITEM (UNCHANGED BUT SAFE)
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

    memory: List[MemoryItem] = field(default_factory=list)

    tool_results: List[ToolResult] = field(default_factory=list)

    llm_response: str | None = None

    meta: Dict[str, Any] = field(default_factory=dict)