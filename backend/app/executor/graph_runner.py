from backend.app.executor.graph import ExecutionGraph


class GraphRunner:

    def __init__(self, executor):
        self.executor = executor

    async def run(self, graph: ExecutionGraph, query: str, user_id: int | None):

        context = {
            "query": query,
            "memory": None,
            "tools": [],
            "llm_input": None
        }

        # -------------------------------------------------
        # STEP EXECUTION LOOP
        # -------------------------------------------------
        for step in graph.steps:

            if step.type == "memory":
                context["memory"] = await self._run_memory(query, user_id)

            elif step.type == "tool":
                result = await self._run_tool(step.name, query)
                context["tools"].append(result)
                step.result = result

            elif step.type == "llm":
                result = await self._run_llm(context)
                step.result = result

        return context

    # -------------------------------------------------
    # MEMORY EXECUTION
    # -------------------------------------------------
    async def _run_memory(self, query, user_id):
        if user_id is None:
            return None

        return self.executor.memory.search(
            user_id=user_id,
            query=query
        )

    # -------------------------------------------------
    # TOOL EXECUTION
    # -------------------------------------------------
    async def _run_tool(self, tool_name, query):

        if tool_name == "file_search":
            return self.executor.file_agent.search(query)

        if tool_name == "system_scanner":
            return self.executor.system_agent.scan(query)

        if tool_name == "rag":
            results = self.executor.rag.search(query)

            if not results:
                return None

            return "\n\n".join(
                item["data"]["chunk"][:500]
                for item in results
            )

        return None

    # -------------------------------------------------
    # LLM EXECUTION
    # -------------------------------------------------
    async def _run_llm(self, context):

        prompt_parts = []

        if context["memory"]:
            prompt_parts.append(context["memory"])

        if context["tools"]:
            prompt_parts.extend(context["tools"])

        prompt_parts.append(context["query"])

        final_prompt = "\n\n".join(prompt_parts)

        return await self.executor.llm.generate(final_prompt)