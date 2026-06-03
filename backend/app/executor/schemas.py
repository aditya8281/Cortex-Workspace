from enum import Enum

from pydantic import BaseModel, Field


class IntentType(str, Enum):
    CHAT = "chat"
    TOOL = "tool"
    SYSTEM = "system"
    RAG = "rag"


class IntentConfidence(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ExecutionPlan(BaseModel):
    intent: IntentType
    use_memory: bool = True
    use_llm: bool = True
    tools: list[str] = Field(default_factory=list)
    tool_candidates: list[str] = Field(default_factory=list)


class ExecutionResult(BaseModel):
    answer: str
    source: str
    memory_used: bool = False

    # -------------------------------------------------
    # EXECUTION OBSERVABILITY
    # -------------------------------------------------
    execution_id: str | None = None


class IntentDecision(BaseModel):
    intent: IntentType
    confidence: float
    confidence_level: IntentConfidence

    subtype: str | None = None
    keywords: list[str] = Field(default_factory=list)

    requires_tools: bool = False