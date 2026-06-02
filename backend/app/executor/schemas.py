from enum import Enum

from pydantic import BaseModel


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
    tools: list[str] = []


class ExecutionResult(BaseModel):
    answer: str
    source: str
    memory_used: bool = False
    
class IntentDecision(BaseModel):
    intent: IntentType
    confidence: float  # 0.0 - 1.0
    confidence_level: IntentConfidence

    subtype: str | None = None  # file_search, system_scan, repo_rag, etc.
    keywords: list[str] = []

    requires_tools: bool = False