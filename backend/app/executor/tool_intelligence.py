from backend.app.executor.context import ToolResult


class ToolIntelligence:

    """
    Responsible for:
    - scoring tool outputs
    - ranking tools
    - filtering noise
    """

    # -------------------------------------------------
    # MAIN ENTRY
    # -------------------------------------------------
    def process(self, tool_results: list[ToolResult]) -> list[ToolResult]:

        if not tool_results:
            return []

        scored = []

        for t in tool_results:
            t.relevance = self._score_relevance(t)
            t.confidence = self._score_confidence(t)
            scored.append(t)

        # sort by importance
        scored.sort(key=lambda x: (x.relevance, x.confidence), reverse=True)

        return scored

    # -------------------------------------------------
    # RELEVANCE SCORING
    # -------------------------------------------------
    def _score_relevance(self, tool: ToolResult) -> float:

        base = 0.5

        # no output → useless
        if tool.output is None:
            return 0.0

        # skipped tool → very low value
        if tool.skipped:
            return 0.1

        # structured output is better
        if isinstance(tool.output, dict):
            base += 0.3

        # large text output (RAG/file search) = more relevant
        if isinstance(tool.output, str) and len(tool.output) > 200:
            base += 0.2

        # tool-specific boosts
        if tool.tool == "rag":
            base += 0.2

        if tool.tool == "file_search":
            base += 0.15

        return min(base, 1.0)

    # -------------------------------------------------
    # CONFIDENCE SCORING
    # -------------------------------------------------
    def _score_confidence(self, tool: ToolResult) -> float:

        if tool.status != "success":
            return 0.2

        if tool.output is None:
            return 0.3

        if isinstance(tool.output, dict):
            return 0.9

        return 0.7