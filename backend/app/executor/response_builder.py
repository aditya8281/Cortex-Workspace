from backend.app.executor.context import ExecutionContext
from backend.app.executor.schemas import ExecutionResult


class ResponseBuilder:

    def build(self, ctx: ExecutionContext) -> ExecutionResult:

        sections = []

        # MEMORY
        if ctx.memory:
            sections.append(self._format_memory(ctx.memory))

        # TOOLS (NOW RANKED)
        if ctx.tool_results:
            sections.append(self._format_tools(ctx.tool_results))

        # LLM
        if ctx.llm_response:
            sections.append(self._format_llm(ctx.llm_response))

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
    # MEMORY
    # -------------------------------------------------
    def _format_memory(self, memory):
        return "🧠 Memory Context:\n" + str(memory)

    # -------------------------------------------------
    # TOOL (RANKED VIEW)
    # -------------------------------------------------
    def _format_tools(self, tool_results):

        # STEP 1: sort by relevance (IMPORTANT NEW LOGIC)
        sorted_tools = sorted(
            tool_results,
            key=lambda t: t.relevance,
            reverse=True
        )

        blocks = ["🛠 Tool Results (Ranked by Relevance):"]

        # STEP 2: render each tool cleanly
        for i, t in enumerate(sorted_tools):

            blocks.append(
                f"""
--- Tool {i + 1} ---
Tool: {t.tool}
Status: {t.status}
Relevance: {t.relevance}
Confidence: {t.confidence}
Output:
{t.output}
"""
            )

        return "\n".join(blocks)

    # -------------------------------------------------
    # LLM
    # -------------------------------------------------
    def _format_llm(self, llm_response):
        return "🤖 Final Response:\n" + str(llm_response)