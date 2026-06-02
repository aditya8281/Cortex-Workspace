from backend.app.executor.context import ToolResult


class ContextCompiler:

    """
    Converts raw tool outputs into LLM-ready reasoning context
    """

    # -------------------------------------------------
    # MAIN ENTRY
    # -------------------------------------------------
    def compile(self, tools: list[ToolResult], memory=None, query="") -> str:

        blocks = []

        # MEMORY BLOCK (compressed)
        if memory:
            blocks.append(self._format_memory(memory))

        # TOOL BLOCKS (structured reasoning)
        if tools:
            blocks.append(self._format_tools(tools))

        # QUERY (always last for grounding)
        blocks.append(f"User Query:\n{query}")

        return "\n\n".join(blocks)

    # -------------------------------------------------
    # MEMORY COMPRESSION
    # -------------------------------------------------
    def _format_memory(self, memory):

        return "🧠 Memory Context:\n" + str(memory)

    # -------------------------------------------------
    # TOOL COMPRESSION (IMPORTANT CORE LOGIC)
    # -------------------------------------------------
    def _format_tools(self, tools):

        blocks = ["🛠 Tool Reasoning Context:"]

        for t in tools:

            blocks.append(
                f"""
Tool: {t.tool}
Status: {t.status}
Relevance: {t.relevance}
Confidence: {t.confidence}

Key Output:
{self._compress_output(t.output)}
"""
            )

        return "\n".join(blocks)

    # -------------------------------------------------
    # OUTPUT COMPRESSION ENGINE
    # -------------------------------------------------
    def _compress_output(self, output):

        if output is None:
            return "None"

        if isinstance(output, str):

            # hard compression (important)
            if len(output) > 800:
                return output[:800] + "\n...[truncated]"
            return output

        if isinstance(output, dict):

            # keep only key-value summary
            keys = list(output.keys())[:8]
            return {
                k: output[k] for k in keys
            }

        return str(output)[:500]