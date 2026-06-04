from backend.app.executor.context import ExecutionContext
from backend.app.executor.schemas import ExecutionResult
from backend.app.tools.base import ToolResult


class ResponseBuilder:
    def build(self, ctx: ExecutionContext) -> ExecutionResult:
        workflow_summary = ctx.meta.get("workflow_summary")
        executed_steps = ctx.meta.get("executed_steps", [])
        tools_used = ctx.meta.get("tools_used", [])
        retrieved_files = ctx.meta.get("retrieved_files", [])
        partial_results = bool(ctx.meta.get("partial_results", False))

        if ctx.llm_response:
            answer = str(ctx.llm_response)
            import re
            pattern = re.compile(r'final\s+response\s*:\s*\n*', re.IGNORECASE)
            parts = pattern.split(answer, 1)
            if len(parts) > 1:
                answer = parts[1]
            return ExecutionResult(
                answer=answer.strip(),
                source="executor_v2",
                memory_used=ctx.memory is not None,
                execution_id=ctx.execution_id,
                routing_info=ctx.routing_info,
                workflow_summary=workflow_summary,
                executed_steps=executed_steps,
                tools_used=tools_used,
                retrieved_files=retrieved_files,
                partial_results=partial_results,
            )

        sections = []

        if ctx.memory:
            sections.append("Memory Context:\n" + str(ctx.memory))

        if ctx.tool_results:
            sections.append(self._format_tools(ctx.tool_results))

        if not sections:
            sections.append("No response or context found.")

        return ExecutionResult(
            answer="\n\n".join(sections),
            source="executor_v2",
            memory_used=ctx.memory is not None,
            execution_id=ctx.execution_id,
            routing_info=ctx.routing_info,
            workflow_summary=workflow_summary,
            executed_steps=executed_steps,
            tools_used=tools_used,
            retrieved_files=retrieved_files,
            partial_results=partial_results,
        )

    def _format_tools(self, tools: list[ToolResult]) -> str:
        blocks = ["Tool Results:"]

        for t in tools:
            if getattr(t, "status", None) in {"error", "skipped"}:
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

    def _compress_meta(self, meta):
        if not meta:
            return {}

        if isinstance(meta, dict):
            return {k: meta[k] for k in list(meta.keys())[:6]}

        return str(meta)[:300]
