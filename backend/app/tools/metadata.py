from dataclasses import dataclass, field


@dataclass
class ToolMetadata:
    name: str
    description: str
    version: str = "1.0.0"

    # capability hints (used by planner later)
    capabilities: list[str] = field(default_factory=list)

    # optional scoring hint for planner
    priority: int = 1

    # optional tags
    tags: list[str] = field(default_factory=list)
