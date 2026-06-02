class ContextCompiler:

    def compile(self, tools, memory=None, query=""):

        blocks = []

        if memory:
            blocks.append("🧠 Memory Context:\n" + str(memory))

        if tools:
            blocks.append(self._format_tools(tools))

        blocks.append("User Query:\n" + query)

        return "\n\n".join(blocks)

    def _format_tools(self, tools):

        blocks = ["🛠 Tool Context:"]

        for t in tools:

            blocks.append(f"""
Tool: {t.get('tool')}
Status: {t.get('status')}
Confidence: {t.get('confidence')}
Relevance: {t.get('relevance')}

Output:
{self._compress_output(t.get('output'))}
""")

        return "\n".join(blocks)

    def _compress_output(self, output):

        if output is None:
            return "None"

        if isinstance(output, str):
            return output[:800]

        if isinstance(output, dict):
            return {k: output[k] for k in list(output.keys())[:6]}

        return str(output)[:500]