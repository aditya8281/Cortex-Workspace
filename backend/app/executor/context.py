from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# -------------------------------------------------
# TOOL RESULT (STRUCTURED, NOT STRING)
# -------------------------------------------------
@dataclass
class ToolResult:
    tool: str
    output: Any
    status: str = "success"
    skipped: bool = False
    reason: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)


# -------------------------------------------------
# MEMORY ITEM (STRUCTURED FUTURE-PROOFING)
# -------------------------------------------------
@dataclass
class MemoryItem:
    content: str
    score: float = 0.0
    source: str = "memory"


# -------------------------------------------------
# EXECUTION CONTEXT (UPGRADED)
# -------------------------------------------------
@dataclass
class ExecutionContext:

    query: str
    user_id: Optional[int] = None

    # MEMORY LAYER
    memory: List[MemoryItem] = field(default_factory=list)

    # TOOL LAYER (STRUCTURED, CRITICAL FIX)
    tool_results: List[ToolResult] = field(default_factory=list)

    # FINAL LLM OUTPUT
    llm_response: Optional[str] = None

    # OPTIONAL: EXECUTION METADATA (FUTURE-PROOF)
    meta: Dict[str, Any] = field(default_factory=dict)