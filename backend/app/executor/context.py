from dataclasses import dataclass, field


@dataclass
class ExecutionContext:
    query: str
    user_id: int | None = None

    memory: str | None = None

    tool_results: list[str] = field(default_factory=list)

    llm_response: str | None = None