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

    """
    Lightweight in-memory learning layer
    (later can be moved to DB)
    """

    def __init__(self):
        self.records: List[ToolFeedbackRecord] = []

    # -------------------------------------------------
    # LOG TOOL USAGE
    # -------------------------------------------------
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

    # -------------------------------------------------
    # GET TOOL BIAS (USED LATER FOR SELECTION)
    # -------------------------------------------------
    def get_tool_bias(self) -> Dict[str, float]:

        bias = {}

        for r in self.records[-200:]:  # last window

            bias.setdefault(r.tool, [])

            score = (r.relevance + r.confidence) / 2
            bias[r.tool].append(score)

        # average score per tool
        return {
            tool: sum(scores) / len(scores)
            for tool, scores in bias.items()
        }
