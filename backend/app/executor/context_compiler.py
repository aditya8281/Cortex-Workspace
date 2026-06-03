class ContextCompiler:
    def compile(self, tools, memory=None, chat_history=None, query=""):
        blocks = []

        if chat_history:
            history_str = "Recent Conversation History:\n"
            for turn in chat_history:
                resp = turn["response"]
                if "Final Response:\n" in resp:
                    resp = resp.split("Final Response:\n", 1)[1]
                history_str += f"User: {turn['query']}\nAssistant: {resp}\n"
            blocks.append(history_str.strip())

        if memory:
            blocks.append("Memory Context:\n" + str(memory))

        if tools:
            blocks.append(self._format_tools(tools))

        blocks.append("User Query:\n" + query)

        return "\n\n".join(blocks)

    def _format_tools(self, tools):
        blocks = ["Tool Context:"]

        for t in tools:
            blocks.append(
                f"""
Tool: {getattr(t, 'tool', 'unknown')}
Status: {getattr(t, 'status', 'unknown')}
Confidence: {getattr(t, 'confidence', 0.0)}
Relevance: {getattr(t, 'relevance', 0.0)}
Skipped: {getattr(t, 'skipped', False)}

Output:
{self._compress_output(getattr(t, 'output', None))}
"""
            )

        return "\n".join(blocks)

    def _compress_output(self, output):
        if output is None:
            return "None"

        if isinstance(output, str):
            return output[:800]

        if isinstance(output, dict):
            return {k: output[k] for k in list(output.keys())[:6]}

        return str(output)[:500]
