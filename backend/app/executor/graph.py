from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExecutionStep:
    id: str
    type: str  # "tool" | "memory" | "llm"
    name: str | None = None
    input: Any = None
    depends_on: list[str] = field(default_factory=list)
    result: Any = None


@dataclass
class ExecutionGraph:
    steps: list[ExecutionStep] = field(default_factory=list)

    def add_step(self, step: ExecutionStep):
        self.steps.append(step)

    def get_step(self, step_id: str) -> ExecutionStep | None:
        for step in self.steps:
            if step.id == step_id:
                return step
        return None