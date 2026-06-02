from backend.app.tools.base import ToolResult


class ToolIntelligence:

    """
    Ranks and filters tool outputs before LLM reasoning.
    This is the "brain filter layer" between tools and LLM.
    """

    def process(self, tools: list[ToolResult]) -> list[ToolResult]:

        if not tools:
            return []

        # -------------------------------------------------
        # STEP 1: FILTER INVALID / LOW QUALITY RESULTS
        # -------------------------------------------------
        filtered = [
            t for t in tools
            if self._is_valid(t)
        ]

        if not filtered:
            return []

        # -------------------------------------------------
        # STEP 2: SCORE EACH TOOL RESULT
        # -------------------------------------------------
        scored = [
            (t, self._score(t))
            for t in filtered
        ]

        # -------------------------------------------------
        # STEP 3: SORT BY SCORE DESC
        # -------------------------------------------------
        scored.sort(key=lambda x: x[1], reverse=True)

        # -------------------------------------------------
        # STEP 4: ATTACH SCORE BACK INTO META
        # -------------------------------------------------
        final = []
        for tool, score in scored:
            tool.meta["intelligence_score"] = score
            final.append(tool)

        return final

    # -------------------------------------------------
    # VALIDATION LAYER
    # -------------------------------------------------
    def _is_valid(self, tool: ToolResult) -> bool:

        if tool is None:
            return False

        if tool.status in ["error"]:
            return False

        if tool.output is None:
            return False

        return True

    # -------------------------------------------------
    # SCORING ENGINE (CORE LOGIC)
    # -------------------------------------------------
    def _score(self, tool: ToolResult) -> float:

        score = 0.0

        # confidence weight
        score += getattr(tool, "confidence", 0.5) * 0.5

        # relevance weight
        score += getattr(tool, "relevance", 0.5) * 0.3

        # output richness
        score += self._output_score(tool.output) * 0.2

        return round(score, 4)

    # -------------------------------------------------
    # OUTPUT QUALITY HEURISTIC
    # -------------------------------------------------
    def _output_score(self, output) -> float:

        if output is None:
            return 0.0

        if isinstance(output, dict):
            return min(len(output.keys()) / 10, 1.0)

        if isinstance(output, list):
            return min(len(output) / 10, 1.0)

        if isinstance(output, str):
            return min(len(output) / 1000, 1.0)

        return 0.5