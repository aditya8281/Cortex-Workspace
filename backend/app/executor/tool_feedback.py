from dataclasses import dataclass, field
from typing import Dict, List
import time

from backend.app.tools.base import ToolResult


@dataclass
class ToolFeedbackRecord:
    tool: str
    query: str
    relevance: float
    confidence: float
    timestamp: float = field(default_factory=time.time)


class ToolFeedbackStore:
    def __init__(self):
        self.records: List[ToolFeedbackRecord] = []

    def log(self, query: str, tools: List[ToolResult]):
        for t in tools:
            self.records.append(
                ToolFeedbackRecord(
                    tool=t.tool,
                    query=query,
                    relevance=t.relevance,
                    confidence=t.confidence
                )
            )

    def get_tool_bias(self) -> Dict[str, float]:
        bias: Dict[str, List[float]] = {}

        for r in self.records[-200:]:

            bias.setdefault(r.tool, [])

            score = (r.relevance + r.confidence) / 2
            bias[r.tool].append(score)

        return {
            tool: sum(scores) / len(scores)
            for tool, scores in bias.items()
        }
