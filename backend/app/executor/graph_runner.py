import asyncio
from typing import Any, Dict, List

from backend.app.executor.graph import ExecutionGraph, ExecutionStep
from backend.app.tools.base import ToolContext


class GraphRunner:
    """
    Deterministic DAG execution engine for Cortex Workspace.
    Executes memory → tools → LLM steps with traceability and stable state.
    """

    def __init__(self, executor):
        self.executor = executor
        self.tools = self.executor.tool_registry
        self.tracer = self.executor.tracer

    # -------------------------------------------------
    # MAIN RUN LOOP
    # -------------------------------------------------
    async def run(
        self,
        graph: ExecutionGraph,
        query: str,
        user_id: int | None,
        plan=None
    ) -> Dict[str, Any]:

        execution_id = self.tracer.create_session()

        state = self._init_state(query, plan)

        pending_steps: List[ExecutionStep] = list(graph.steps)

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

                self._apply_step_result(step, result, state)
                pending_steps.remove(step)

        return state

    # -------------------------------------------------
    # STATE INITIALIZATION
    # -------------------------------------------------
    def _init_state(self, query: str, plan) -> Dict[str, Any]:

        state = {
            "query": query,

            # deterministic execution tracking
            "completed": [],
            "step_results": {},

            # execution outputs
            "memory": None,
            "tools": [],
            "llm": None,

            # agentic extensions
            "tool_candidates": [],
            "tool_decisions": {}
        }

        if plan and hasattr(plan, "tool_candidates"):
            state["tool_candidates"] = plan.tool_candidates

        return state

    # -------------------------------------------------
    # DAG READY CHECK
    # -------------------------------------------------
    def _is_ready(self, step: ExecutionStep, state: Dict[str, Any]) -> bool:
        return all(dep in state["completed"] for dep in step.depends_on)

    # -------------------------------------------------
    # APPLY RESULTS TO STATE (SINGLE SOURCE OF TRUTH)
    # -------------------------------------------------
    def _apply_step_result(self, step: ExecutionStep, result: Any, state: Dict[str, Any]):

        state["completed"].append(step.id)
        state["step_results"][step.id] = result
        step.result = result

        if step.type == "memory":
            state["memory"] = result

        elif step.type == "tool":
            normalized = self._normalize_tool_output(result)
            if normalized:
                state["tools"].append(normalized)

        elif step.type == "llm":
            state["llm"] = result

    # -------------------------------------------------
    # STEP EXECUTOR
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

            return {
                "status": "error",
                "error": str(e),
                "step": step.id
            }

    # -------------------------------------------------
    # MEMORY STEP (RAW RETRIEVAL ONLY)
    # -------------------------------------------------
    async def _run_memory(self, query, user_id):

        if user_id is None:
            return None

        return self.executor.memory.search(
            user_id=user_id,
            query=query
        )

    # -------------------------------------------------
    # TOOL EXECUTION (DECIDE → RUN → REFLECT)
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
            return {
                "tool": tool_name,
                "status": "missing",
                "output": None
            }

        context = ToolContext(
            user_id=user_id,
            query=query,
            state=state
        )

        decision = tool.decide(context)

        self.tracer.log_event(
            "tool_decision",
            {
                "tool": tool_name,
                "decision": decision
            }
        )

        if not decision.get("should_run", True):
            return {
                "tool": tool_name,
                "status": "skipped",
                "reason": decision.get("reason", "no reason"),
                "output": None
            }

        try:
            result = await tool.run(
                context,
                decision.get("params", {})
            )

            reflection = tool.reflect(result)

            state["tool_decisions"][tool_name] = decision

            self.tracer.log_event(
                "tool_result",
                {
                    "tool": tool_name,
                    "reflection": reflection
                }
            )

            return {
                "tool": tool_name,
                "status": "success",
                "output": result,
                "reflection": reflection
            }

        except Exception as e:

            return {
                "tool": tool_name,
                "status": "error",
                "output": None,
                "error": str(e)
            }

    # -------------------------------------------------
    # LLM FINAL SYNTHESIS STEP
    # -------------------------------------------------
    async def _run_llm(self, state, query):

        prompt_parts = []

        # memory
        if state["memory"]:
            prompt_parts.append(str(state["memory"]))

        # tool outputs (clean + deterministic)
        for tool_result in state["tools"]:
            prompt_parts.append(str(tool_result))

        # user query last
        prompt_parts.append(query)

        final_prompt = "\n\n".join(prompt_parts)

        return await self.executor.llm.generate(final_prompt)

    # -------------------------------------------------
    # NORMALIZATION
    # -------------------------------------------------
    def _normalize_tool_output(self, result):

        if not result:
            return None

        if isinstance(result, dict):
            if result.get("status") == "error":
                return f"[TOOL_ERROR] {result.get('error', 'unknown error')}"
            return str(result.get("output", result))

        return str(result)