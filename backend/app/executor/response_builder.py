from backend.app.executor.context import ExecutionContext
from backend.app.executor.schemas import ExecutionResult


class ResponseBuilder:

    def build(self, ctx: ExecutionContext) -> ExecutionResult:

        sections = []

        # -------------------------------------------------
        # MEMORY LAYER (contextual, lowest priority)
        # -------------------------------------------------
        if ctx.memory:
            sections.append(
                "🧠 Memory Context:\n" + ctx.memory
            )

        # -------------------------------------------------
        # TOOL LAYER (ground truth, medium priority)
        # -------------------------------------------------
        if ctx.tool_results:
            tool_block = "\n\n".join(ctx.tool_results)
            sections.append(
                "🛠 Tool Results:\n" + tool_block
            )

        # -------------------------------------------------
        # LLM LAYER (final reasoning, highest priority)
        # -------------------------------------------------
        if ctx.llm_response:
            sections.append(
                "🤖 Final Response:\n" + ctx.llm_response
            )

        # -------------------------------------------------
        # SAFETY: fallback if everything empty
        # -------------------------------------------------
        if not sections:
            sections.append(
                "🤖 Final Response:\nI couldn't generate a response from available context."
            )

        return ExecutionResult(
            answer="\n\n".join(sections),
            source="executor_v2",
            memory_used=ctx.memory is not None
        )