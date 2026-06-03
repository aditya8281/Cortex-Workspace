from backend.app.tools.base import ToolResult


class ToolIntelligence:
    def process(self, tools: list[ToolResult]) -> list[ToolResult]:
        if not tools:
            return []

        filtered = [
            t for t in tools
            if self._is_valid(t)
        ]

        if not filtered:
            return []

        scored = [
            (t, self._score(t))
            for t in filtered
        ]

        scored.sort(key=lambda x: x[1], reverse=True)

        final = []
        for tool, score in scored:
            if isinstance(tool.meta, dict):
                tool.meta["intelligence_score"] = score
            final.append(tool)

        return final

    def _is_valid(self, tool: ToolResult) -> bool:
        if tool is None:
            return False

        if tool.status in {"error", "skipped"}:
            return False

        if tool.output is None:
            return False

        return True

    def _score(self, tool: ToolResult) -> float:
        score = 0.0
        score += getattr(tool, "confidence", 0.5) * 0.5
        score += getattr(tool, "relevance", 0.5) * 0.3
        score += self._output_score(tool.output) * 0.2

        return round(score, 4)

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
