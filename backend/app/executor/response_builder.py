from backend.app.executor.context import ExecutionContext
from backend.app.executor.schemas import ExecutionResult


class ResponseBuilder:

    def build(self, ctx: ExecutionContext) -> ExecutionResult:

        sections = []

        # -------------------------------------------------
        # MEMORY LAYER (contextual grounding)
        # -------------------------------------------------
        if ctx.memory:
            sections.append(
                self._format_memory(ctx.memory)
            )

        # -------------------------------------------------
        # TOOL LAYER (structured grounding)
        # -------------------------------------------------
        if ctx.tool_results:
            sections.append(
                self._format_tools(ctx.tool_results)
            )

        # -------------------------------------------------
        # LLM LAYER (final reasoning)
        # -------------------------------------------------
        if ctx.llm_response:
            sections.append(
                self._format_llm(ctx.llm_response)
            )

        # -------------------------------------------------
        # FALLBACK
        # -------------------------------------------------
        if not sections:
            sections.append(
                "🤖 Final Response:\nI couldn't generate a response from available context."
            )

        return ExecutionResult(
            answer="\n\n".join(sections),
            source="executor_v2",
            memory_used=bool(ctx.memory)
        )

    # -------------------------------------------------
    # MEMORY FORMATTING
    # -------------------------------------------------
    def _format_memory(self, memory):

        return "🧠 Memory Context:\n" + str(memory)

    # -------------------------------------------------
    # TOOL FORMATTING (IMPORTANT UPGRADE)
    # -------------------------------------------------
    def _format_tools(self, tool_results):

        blocks = ["🛠 Tool Results:"]

        for i, tool in enumerate(tool_results):

            blocks.append(
                f"\n--- Tool {i + 1} ---\n{self._serialize_tool(tool)}"
            )

        return "\n".join(blocks)

    # -------------------------------------------------
    # TOOL SERIALIZATION (CRITICAL FIX)
    # -------------------------------------------------
    def _serialize_tool(self, tool):

        # already structured dict (new system)
        if isinstance(tool, dict):

            parts = []

            for k, v in tool.items():

                if v is None:
                    continue

                if isinstance(v, (list, dict)):
                    parts.append(f"{k}: {v}")
                else:
                    parts.append(f"{k}: {str(v)}")

            return "\n".join(parts)

        # fallback
        return str(tool)

    # -------------------------------------------------
    # LLM FORMATTING
    # -------------------------------------------------
    def _format_llm(self, llm_response):

        return "🤖 Final Response:\n" + str(llm_response)