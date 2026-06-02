from enum import Enum

from pydantic import BaseModel


class IntentType(str, Enum):
    CHAT = "chat"
    TOOL = "tool"
    SYSTEM = "system"
    RAG = "rag"


class ExecutionPlan(BaseModel):
    intent: IntentType
    use_memory: bool = True
    use_llm: bool = True
    tools: list[str] = []


class ExecutionResult(BaseModel):
    answer: str
    source: str
    memory_used: bool = False