import asyncio
from backend.app.executor.graph import ExecutionGraph, ExecutionStep
from backend.app.tools.base import ToolContext, ToolResult
from backend.app.executor.tool_intelligence import ToolIntelligence
from backend.app.executor.tool_fusion import ToolFusionEngine
from backend.app.executor.context_compiler import ContextCompiler

from backend.app.state.manager import StateManager
from backend.app.state.models import SystemEvent, EventType


class GraphRunner:

    def __init__(self, executor):
        self.executor = executor
        self.tools = self.executor.tool_registry
        self.tracer = self.executor.tracer
        self.state = StateManager()

    # -------------------------------------------------
    # MAIN EXECUTION LOOP
    # -------------------------------------------------
    async def run(self, graph: ExecutionGraph, query: str, user_id: int | None):

        state = {
            "query": query,
            "memory": None,
            "tools": [],
            "tool_map": {},
            "llm": None,
            "completed": set(),
            "execution_trace": []
        }

        execution_id = self.tracer.create_session()

        # 🔥 CRITICAL FIX: bind execution context
        self.state.set_execution_id(execution_id)

        pending_steps = graph.steps.copy()

        # -------------------------------------------------
        # GRAPH START EVENT
        # -------------------------------------------------
        self.state.emit_event(SystemEvent(
            type=EventType.TOOL_EXECUTED,
            payload={
                "stage": "graph_execution_start",
                "execution_id": execution_id,
                "query": query,
                "steps": len(graph.steps)
            },
            source="GraphRunner"
        ))

        try:

            while pending_steps:

                ready_steps = [
                    s for s in pending_steps
                    if self._is_ready(s, state)
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

                    state["execution_trace"].append({
                        "step_id": step.id,
                        "type": step.type,
                        "name": step.name,
                        "depends_on": step.depends_on,
                        "result": str(result)[:500]
                    })

                    if step.type == "memory":
                        state["memory"] = result

                    elif step.type == "tool":
                        tool_result = self._normalize_tool(result)
                        if tool_result:
                            state["tools"].append(tool_result)

                    elif step.type == "llm":
                        state["llm"] = result

                    pending_steps.remove(step)

            # -------------------------------------------------
            # POST PROCESSING
            # -------------------------------------------------
            state["tools"] = ToolIntelligence().process(state["tools"])
            state["tools"] = ToolFusionEngine().process(state["tools"])

            # -------------------------------------------------
            # GRAPH END EVENT
            # -------------------------------------------------
            self.state.emit_event(SystemEvent(
                type=EventType.EXECUTION_COMPLETED,
                payload={
                    "execution_id": execution_id,
                    "query": query,
                    "tool_count": len(state["tools"]),
                    "steps_executed": len(state["execution_trace"]),
                    "status": "success"
                },
                source="GraphRunner"
            ))

            return state

        finally:
            # 🔥 CRITICAL CLEANUP
            self.state.clear_execution_id()

    # -------------------------------------------------
    # READY CHECK
    # -------------------------------------------------
    def _is_ready(self, step: ExecutionStep, state) -> bool:
        return all(dep in state["completed"] for dep in step.depends_on)

    # -------------------------------------------------
    # STEP EXECUTION
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

            self.state.emit_event(SystemEvent(
                type=EventType.TOOL_EXECUTED,
                payload={
                    "stage": "step_start",
                    "step_id": step.id,
                    "type": step.type,
                    "name": step.name
                },
                source="GraphRunner"
            ))

            if step.type == "memory":
                result = await self._run_memory(query, user_id)

            elif step.type == "tool":
                result = await self._run_tool(step.name, query, state, user_id)

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

            self.state.emit_event(SystemEvent(
                type=EventType.EXECUTION_COMPLETED,
                payload={
                    "execution_id": execution_id,
                    "step_id": step.id,
                    "status": "step_failed",
                    "error": str(e)
                },
                source="GraphRunner"
            ))

            return ToolResult(
                tool=step.name or "unknown",
                output=None,
                confidence=0.0,
                relevance=0.0,
                status="error",
                meta={"error": str(e)}
            )

    # -------------------------------------------------
    # MEMORY
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
    async def _run_tool(self, tool_name, query, state, user_id):

        tool = self.tools.get(tool_name)

        if not tool:
            return ToolResult(
                tool=tool_name,
                output=None,
                confidence=0.0,
                relevance=0.0,
                status="error",
                meta={"reason": "tool_not_found"}
            )

        context = ToolContext(
            user_id=user_id,
            query=query,
            state=state
        )

        decision = tool.decide(context)

        if not decision.get("should_run"):
            return ToolResult(
                tool=tool_name,
                output=None,
                confidence=1.0,
                relevance=0.0,
                status="skipped",
                meta={"reason": decision.get("reason", "no reason")}
            )

        raw_output = await tool.run(
            context,
            decision.get("params", {})
        )

        reflection = tool.reflect(raw_output)

        return ToolResult(
            tool=tool_name,
            output=raw_output,
            confidence=decision.get("confidence", 1.0),
            relevance=1.0,
            status="success",
            meta={
                "reflection": reflection,
                "params": decision.get("params", {})
            }
        )

    # -------------------------------------------------
    # NORMALIZER
    # -------------------------------------------------
    def _normalize_tool(self, result):

        if result is None:
            return None

        if isinstance(result, ToolResult):
            return result

        return ToolResult(
            tool="unknown",
            output=result,
            confidence=1.0,
            relevance=1.0,
            status="success",
            meta={"wrapped": True}
        )

    # -------------------------------------------------
    # LLM
    # -------------------------------------------------
    async def _run_llm(self, state, query):

        compiler = ContextCompiler()

        prompt = compiler.compile(
            tools=state["tools"],
            memory=state["memory"],
            query=query
        )

        return await self.executor.llm.generate(prompt)