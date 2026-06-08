from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class WorkflowStepPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    tool: str
    args: dict[str, Any] = Field(default_factory=dict)
    depends_on: list[int] = Field(default_factory=list)
    fallback_tools: list[str] = Field(default_factory=list)
    critical: bool = True
    description: str | None = None


class WorkflowPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    goal: str
    steps: list[WorkflowStepPlan] = Field(default_factory=list)


@dataclass(slots=True)
class WorkflowNode:
    id: str
    step_id: int
    tool: str
    args: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    fallback_tools: list[str] = field(default_factory=list)
    critical: bool = True
    description: str | None = None


@dataclass(slots=True)
class WorkflowGraph:
    nodes: list[WorkflowNode] = field(default_factory=list)
    edges: list[tuple[str, str]] = field(default_factory=list)
    layers: list[list[str]] = field(default_factory=list)
    plan: WorkflowPlan | None = None

    def get_node(self, node_id: str) -> WorkflowNode | None:
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def node_ids(self) -> list[str]:
        return [node.id for node in self.nodes]


@dataclass(slots=True)
class WorkflowStepLog:
    step_id: str
    tool: str
    dependencies: list[str] = field(default_factory=list)
    input: dict[str, Any] = field(default_factory=dict)
    output: Any = None
    duration_ms: float = 0.0
    status: str = "pending"
    attempts: int = 0
    fallback_used: str | None = None
    error: str | None = None


@dataclass(slots=True)
class WorkflowState:
    execution_id: str
    query: str
    user_id: int | None = None
    intent: Any = None
    llm_model: str | None = None
    inference_engine: str | None = None
    api_key: str | None = None
    api_base_url: str | None = None
    history: list | None = None
    context_items: list | None = None
    permissions: dict[str, bool] = field(default_factory=dict)
    step_results: dict[str, Any] = field(default_factory=dict)
    file_cache: dict[str, str] = field(default_factory=dict)
    retrieved_context: dict[str, Any] = field(default_factory=dict)
    intermediate_outputs: dict[str, Any] = field(default_factory=dict)
    retrieved_files: list[str] = field(default_factory=list)
    execution_logs: list[WorkflowStepLog] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)
    completed_steps: list[str] = field(default_factory=list)
    final_response: str | None = None
    summary: dict[str, Any] = field(default_factory=dict)

    def to_runtime_state(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "query": self.query,
            "user_id": self.user_id,
            "intent": self.intent,
            "llm_model": self.llm_model,
            "inference_engine": self.inference_engine,
            "api_key": self.api_key,
            "api_base_url": self.api_base_url,
            "history": self.history,
            "context_items": self.context_items,
            "permissions": self.permissions,
            "step_results": self.step_results,
            "file_cache": self.file_cache,
            "retrieved_context": self.retrieved_context,
            "intermediate_outputs": self.intermediate_outputs,
            "retrieved_files": self.retrieved_files,
            "execution_logs": self.execution_logs,
            "errors": self.errors,
            "completed_steps": self.completed_steps,
            "final_response": self.final_response,
            "summary": self.summary,
        }
