from dataclasses import dataclass, field
from typing import Any, Literal


StepType = Literal["tool", "memory", "llm"]


@dataclass
class ExecutionStep:
    id: str
    type: StepType
    name: str | None = None
    input: Any = None
    depends_on: list[str] = field(default_factory=list)
    result: Any = None


@dataclass
class ExecutionGraph:
    steps: list[ExecutionStep] = field(default_factory=list)

    # -------------------------------------------------
    # ADD STEP (WITH BASIC SAFETY)
    # -------------------------------------------------
    def add_step(self, step: ExecutionStep):

        if self.get_step(step.id):
            raise ValueError(f"Duplicate step id detected: {step.id}")

        self.steps.append(step)

    # -------------------------------------------------
    # GET STEP
    # -------------------------------------------------
    def get_step(self, step_id: str) -> ExecutionStep | None:
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    # -------------------------------------------------
    # VALIDATION (CRITICAL FOR STABILITY)
    # -------------------------------------------------
    def validate(self) -> None:

        step_ids = {s.id for s in self.steps}

        # 1. check invalid dependencies
        for step in self.steps:
            for dep in step.depends_on:
                if dep not in step_ids:
                    raise ValueError(
                        f"Invalid dependency '{dep}' in step '{step.id}'"
                    )

        # 2. detect self-dependency
        for step in self.steps:
            if step.id in step.depends_on:
                raise ValueError(
                    f"Self dependency detected in step '{step.id}'"
                )

        # 3. detect cycles (DFS)
        visited = set()
        stack = set()

        def dfs(node_id: str):
            if node_id in stack:
                raise ValueError(f"Cycle detected at '{node_id}'")

            if node_id in visited:
                return

            visited.add(node_id)
            stack.add(node_id)

            node = self.get_step(node_id)
            if node:
                for dep in node.depends_on:
                    dfs(dep)

            stack.remove(node_id)

        for step in self.steps:
            dfs(step.id)

    # -------------------------------------------------
    # TOPOLOGICAL ORDER (OPTIONAL BUT USEFUL)
    # -------------------------------------------------
    def sorted_steps(self) -> list[ExecutionStep]:

        visited = set()
        result = []

        def visit(step: ExecutionStep):
            if step.id in visited:
                return

            for dep_id in step.depends_on:
                dep = self.get_step(dep_id)
                if dep:
                    visit(dep)

            visited.add(step.id)
            result.append(step)

        for step in self.steps:
            visit(step)

        return result