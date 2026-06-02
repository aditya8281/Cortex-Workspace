from backend.app.executor.context import ToolResult


class ToolFusionEngine:

    """
    Responsible for:
    - detecting conflicts
    - merging redundant tool outputs
    - producing clean reasoning signal for LLM
    """

    # -------------------------------------------------
    # MAIN ENTRY
    # -------------------------------------------------
    def process(self, tools: list[ToolResult]) -> list[ToolResult]:

        if not tools:
            return []

        tools = self._remove_nulls(tools)
        tools = self._merge_duplicates(tools)
        tools = self._resolve_conflicts(tools)

        return tools

    # -------------------------------------------------
    # REMOVE EMPTY OUTPUTS
    # -------------------------------------------------
    def _remove_nulls(self, tools):
        return [
            t for t in tools
            if t.output is not None and not t.skipped
        ]

    # -------------------------------------------------
    # MERGE DUPLICATES (same tool + similar output)
    # -------------------------------------------------
    def _merge_duplicates(self, tools):

        merged = []
        seen = {}

        for t in tools:

            key = t.tool

            if key not in seen:
                seen[key] = t
                continue

            existing = seen[key]

            # merge logic
            existing.output = self._merge_outputs(
                existing.output,
                t.output
            )

            existing.relevance = max(
                existing.relevance,
                t.relevance
            )

        return list(seen.values())

    # -------------------------------------------------
    # SIMPLE CONFLICT RESOLUTION
    # -------------------------------------------------
    def _resolve_conflicts(self, tools):

        # rule-based resolution (v1)

        high_priority = ["rag", "file_search"]

        resolved = []

        for t in tools:

            # prioritize core knowledge tools
            if t.tool in high_priority:
                t.conflict_score = 1.0
            else:
                t.conflict_score = 0.5

            resolved.append(t)

        # sort by final importance
        resolved.sort(
            key=lambda x: (x.relevance, x.conflict_score),
            reverse=True
        )

        return resolved

    # -------------------------------------------------
    # OUTPUT MERGER
    # -------------------------------------------------
    def _merge_outputs(self, a, b):

        if isinstance(a, str) and isinstance(b, str):
            return a + "\n\n" + b

        if isinstance(a, dict) and isinstance(b, dict):
            return {**a, **b}

        return a if len(str(a)) > len(str(b)) else b