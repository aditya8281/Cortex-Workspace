class ContextCompiler:
    def compile(self, tools, memory=None, chat_history=None, query="", context_items=None):
        blocks = []

        # Add attached context items first (highest priority)
        if context_items:
            context_block = self._format_context_items(context_items)
            if context_block:
                blocks.append(context_block)

        if chat_history:
            import re
            pattern = re.compile(r'final\s+response\s*:\s*\n*', re.IGNORECASE)
            history_str = "Recent Conversation History:\n"
            for turn in chat_history:
                if isinstance(turn, dict) and "query" in turn and "response" in turn:
                    q = turn["query"]
                    resp = turn["response"]
                    parts = pattern.split(resp, 1)
                    if len(parts) > 1:
                        resp = parts[1]
                    history_str += f"User: {q}\nAssistant: {resp}\n"
                elif isinstance(turn, dict) and "role" in turn and "content" in turn:
                    role_display = "User" if turn["role"] == "user" else "Assistant"
                    content = turn["content"]
                    parts = pattern.split(content, 1)
                    if len(parts) > 1:
                        content = parts[1]
                    history_str += f"{role_display}: {content}\n"
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

    def _format_context_items(self, context_items):
        """Format attached context items into a structured prompt block."""
        if not context_items:
            return None

        blocks = ["=== Attached Context ==="]
        for item in context_items:
            kind = getattr(item, "kind", "unknown")
            title = getattr(item, "title", "")
            header = f"\n[{kind.upper()}] {title}"
            blocks.append(header)

            # Prefer resolved content > content_preview > detail > path/url
            resolved = getattr(item, "resolved_content", None)
            preview = getattr(item, "content_preview", None)
            detail = getattr(item, "detail", None)
            path = getattr(item, "path", None)
            url = getattr(item, "url", None)

            if resolved:
                blocks.append(resolved[:6000])
            elif preview:
                blocks.append(preview[:3000])
            elif detail:
                blocks.append(detail)

            if path and not resolved:
                blocks.append(f"Path: {path}")
            if url and not resolved:
                blocks.append(f"URL: {url}")

        blocks.append("=== End of Attached Context ===")
        return "\n".join(blocks)
