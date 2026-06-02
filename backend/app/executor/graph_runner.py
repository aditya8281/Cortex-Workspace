import asyncio
from backend.app.executor.graph import ExecutionGraph, ExecutionStep
from backend.app.tools.base import ToolContext


class GraphRunner:

    def __init__(self, executor):
        self.executor = executor
        self.tools = self.executor.tool_registry
        self.tracer = self.executor.tracer

    # -------------------------------------------------
    # MAIN RUN METHOD (NOW TOOL-AWARE + PLAN-AWARE)
    # -------------------------------------------------
    async def run(
        self,
        graph: ExecutionGraph,
        query: str,
        user_id: int | None,
        plan=None
    ):

        # -------------------------------------------------
        # EXECUTION STATE
        # -------------------------------------------------
        state = {
            "query": query,
            "memory": None,
            "tools": [],
            "tool_map": {},
            "llm": None,
            "completed": set(),

            # agentic extensions
            "tool_candidates": [],
            "tool_decisions": {}
        }

        if plan and hasattr(plan, "tool_candidates"):
            state["tool_candidates"] = plan.tool_candidates

        pending_steps = graph.steps.copy()

        execution_id = self.tracer.create_session()

        # -------------------------------------------------
        # DAG EXECUTION LOOP
        # -------------------------------------------------
        while pending_steps:

            ready_steps = [
                step for step in pending_steps
                if self._is_ready(step, state)
            ]

            if not ready_steps:
                break

            results = await asyncio.gather(
                *[
                    self._execute_step(
                        execution_id,
                        step,
                        state,
                        query,
                        user_id
                    )
                    for step in ready_steps
                ],
                return_exceptions=True
            )

            for step, result in zip(ready_steps, results):

                state["completed"].add(step.id)
                state["tool_map"][step.id] = result
                step.result = result

                if step.type == "memory":
                    state["memory"] = result

                elif step.type == "tool":
                    state["tools"].append(result)

                elif step.type == "llm":
                    state["llm"] = result

                pending_steps.remove(step)

        return state

    # -------------------------------------------------
    # DAG READY CHECK
    # -------------------------------------------------
    def _is_ready(self, step: ExecutionStep, state) -> bool:
        return all(dep in state["completed"] for dep in step.depends_on)

    # -------------------------------------------------
    # STEP EXECUTION ROUTER
    # -------------------------------------------------
    async def _execute_step(
        self,
        execution_id,
        step,
        state,
        query,
        user_id
    ):

        self.tracer.start(
            execution_id,
            step.id,
            step.type,
            step.name
        )

        try:

            if step.type == "memory":
                result = await self._run_memory(query, user_id)

            elif step.type == "tool":
                result = await self._run_tool_autonomous(
                    step.name,
                    query,
                    state,
                    user_id
                )

            elif step.type == "llm":
                result = await self._run_llm(state, query)

            else:
                result = None

            self.tracer.end(
                execution_id,
                step.id,
                result=result
            )

            return result

        except Exception as e:

            self.tracer.end(
                execution_id,
                step.id,
                error=str(e)
            )

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
    # TOOL BRAIN EXECUTION (NEW CORE LOGIC)
    # -------------------------------------------------
    async def _run_tool_autonomous(
        self,
        tool_name,
        query,
        state,
        user_id
    ):

        tool = self.tools.tools.get(tool_name)

        if not tool:
            return None

        context = ToolContext(
            user_id=user_id,
            query=query,
            state=state
        )

        # 1. TOOL DECISION (BRAIN)
        decision = tool.decide(context)

        self.tracer.log_event(
            "tool_decision",
            {
                "tool": tool_name,
                "decision": decision
            }
        )

        # 2. SKIP IF NOT NEEDED
        if not decision.get("should_run"):
            return {
                "tool": tool_name,
                "skipped": True,
                "reason": decision.get("reason", "no reason")
            }

        # 3. EXECUTE TOOL
        result = await tool.run(
            context,
            decision.get("params", {})
        )

        # 4. REFLECTION (lightweight feedback layer)
        reflection = tool.reflect(result)

        self.tracer.log_event(
            "tool_result",
            {
                "tool": tool_name,
                "reflection": reflection
            }
        )

        state["tool_decisions"][tool_name] = decision

        return {
            "tool": tool_name,
            "output": result,
            "reflection": reflection
        }

    # -------------------------------------------------
    # LLM STEP (FINAL SYNTHESIS)
    # -------------------------------------------------
    async def _run_llm(self, state, query):

        prompt_parts = []

        if state["memory"]:
            prompt_parts.append(str(state["memory"]))

        for step_id in sorted(state["tool_map"].keys()):
            if not step_id.startswith("tool_step_"):
                continue

            value = state["tool_map"][step_id]
            if value:
                prompt_parts.append(str(value))

        prompt_parts.append(query)

        final_prompt = "\n\n".join(prompt_parts)

        return await self.executor.llm.generate(final_prompt)