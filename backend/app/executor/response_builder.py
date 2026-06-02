from backend.app.executor.context import ExecutionContext
from backend.app.executor.schemas import ExecutionResult


class ResponseBuilder:

    def build(
        self,
        ctx: ExecutionContext
    ) -> ExecutionResult:

        sections = []

        if ctx.memory:
            sections.append(ctx.memory)

        if ctx.tool_results:
            sections.extend(ctx.tool_results)

        if ctx.llm_response:
            sections.append(ctx.llm_response)

        return ExecutionResult(
            answer="\n\n".join(sections),
            source="executor",
            memory_used=ctx.memory is not None
        )