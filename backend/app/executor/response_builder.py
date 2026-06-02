from backend.app.executor.context import ExecutionContext
from backend.app.executor.schemas import ExecutionResult
from backend.app.tools.base import ToolResult


class ResponseBuilder:

    def build(self, ctx: ExecutionContext) -> ExecutionResult:

        sections = []

        # -------------------------------------------------
        # MEMORY LAYER (low priority, contextual grounding)
        # -------------------------------------------------
        if ctx.memory:
            sections.append(
                "🧠 Memory Context:\n" + str(ctx.memory)
            )

        # -------------------------------------------------
        # TOOL LAYER (structured + confidence-aware)
        # -------------------------------------------------
        if ctx.tool_results:
            tool_block = self._format_tools(ctx.tool_results)
            sections.append(tool_block)

        # -------------------------------------------------
        # LLM LAYER (final reasoning output)
        # -------------------------------------------------
        if ctx.llm_response:
            sections.append(
                "🤖 Final Response:\n" + str(ctx.llm_response)
            )

        # -------------------------------------------------
        # FALLBACK
        # -------------------------------------------------
        if not sections:
            sections.append(
                "🤖 Final Response:\nNo usable context found to generate response."
            )

        return ExecutionResult(
            answer="\n\n".join(sections),
            source="executor_v2",
            memory_used=ctx.memory is not None
        )

    # -------------------------------------------------
    # TOOL FORMATTING ENGINE (IMPORTANT UPGRADE)
    # -------------------------------------------------
    def _format_tools(self, tools: list[ToolResult]) -> str:

        blocks = ["🛠 Tool Results (Structured):"]

        for t in tools:

            # skip low-quality / failed tools
            if getattr(t, "status", None) in ["error"]:
                continue

            blocks.append(
                f"""
Tool: {t.tool}
Status: {t.status}
Confidence: {t.confidence}
Relevance: {t.relevance}

Output:
{self._compress_output(t.output)}

Meta:
{self._compress_meta(t.meta)}
"""
            )

        return "\n".join(blocks)

    # -------------------------------------------------
    # OUTPUT COMPRESSION
    # -------------------------------------------------
    def _compress_output(self, output):

        if output is None:
            return "None"

        if isinstance(output, str):
            return output[:800] + ("\n...[truncated]" if len(output) > 800 else "")

        if isinstance(output, dict):
            keys = list(output.keys())[:6]
            return {k: output[k] for k in keys}

        if isinstance(output, list):
            return output[:5]

        return str(output)[:500]

    # -------------------------------------------------
    # META COMPRESSION
    # -------------------------------------------------
    def _compress_meta(self, meta):

        if not meta:
            return {}

        if isinstance(meta, dict):
            return {k: meta[k] for k in list(meta.keys())[:6]}

        return str(meta)[:300]