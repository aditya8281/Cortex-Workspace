from enum import Enum

from pydantic import BaseModel


class IntentType(str, Enum):
    CHAT = "chat"
    TOOL = "tool"
    SYSTEM = "system"


class ExecutionPlan(BaseModel):
    intent: IntentType
    use_memory: bool = True
    tool_name: str | None = None


class ExecutionResult(BaseModel):
    answer: str
    source: str
    memory_used: bool = False