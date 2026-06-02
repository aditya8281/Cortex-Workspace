import asyncio
from backend.app.executor.graph import ExecutionGraph, ExecutionStep


class GraphRunner:

    def __init__(self, executor):
        self.executor = executor
        self.tools = self.executor.tool_registry

    async def run(self, graph: ExecutionGraph, query: str, user_id: int | None):

        # -------------------------------------------------
        # EXECUTION STATE (clean + structured)
        # -------------------------------------------------
        state = {
            "query": query,
            "memory": None,
            "tool_map": {},      # step_id -> result
            "llm": None,
            "completed": set()
        }

        pending_steps = graph.steps.copy()

        # -------------------------------------------------
        # DAG EXECUTION LOOP
        # -------------------------------------------------
        while pending_steps:

            ready_steps = [
                step for step in pending_steps
                if self._is_ready(step, state)
            ]

            if not ready_steps:
                break  # prevents deadlock

            results = await asyncio.gather(
                *[
                    self._execute_step(step, state, query, user_id)
                    for step in ready_steps
                ],
                return_exceptions=True
            )

            for step, result in zip(ready_steps, results):

                state["completed"].add(step.id)
                state["tool_map"][step.id] = result
                step.result = result

                pending_steps.remove(step)

        return state

    # -------------------------------------------------
    # DAG RESOLUTION
    # -------------------------------------------------
    def _is_ready(self, step: ExecutionStep, state) -> bool:

        return all(dep in state["completed"] for dep in step.depends_on)

    # -------------------------------------------------
    # STEP EXECUTION ROUTER
    # -------------------------------------------------
    async def _execute_step(self, step, state, query, user_id):

        try:

            if step.type == "memory":
                return await self._run_memory(query, user_id)

            if step.type == "tool":
                return await self._run_tool(step.name, query)

            if step.type == "llm":
                return await self._run_llm(state, query)

            return None

        except Exception as e:
            return f"ERROR: {str(e)}"

    # -------------------------------------------------
    # MEMORY STEP
    # -------------------------------------------------
    async def _run_memory(self, query, user_id):

        if user_id is None:
            return None

        return self.executor.memory.search(
            user_id=user_id,
            query=query
        )

    # -------------------------------------------------
    # TOOL STEP (NOW PROPERLY DELEGATED)
    # -------------------------------------------------
    async def _run_tool(self, tool_name, query):

        return await self.tools.execute(tool_name, query)

    # -------------------------------------------------
    # LLM STEP (DEPENDENCY-AWARE)
    # -------------------------------------------------
    async def _run_llm(self, state, query):

        prompt_parts = []

        # memory first
        if state["memory"]:
            prompt_parts.append(state["memory"])

        # tool outputs (ordered deterministically)
        for step_id in sorted(state["tool_map"].keys()):
            value = state["tool_map"][step_id]
            if value:
                prompt_parts.append(str(value))

        prompt_parts.append(query)

        final_prompt = "\n\n".join(prompt_parts)

        return await self.executor.llm.generate(final_prompt)