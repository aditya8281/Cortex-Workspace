from backend.app.state.manager import StateManager
from backend.app.state.models import SystemEvent, EventType


class AIExecutor:
    """
    Core execution engine for Cortex AI system.
    Now enhanced with system state observability layer.
    """

    def __init__(self, tool_registry=None, tracer=None):
        self.tool_registry = tool_registry
        self.tracer = tracer

        # 🧠 SYSTEM STATE KERNEL
        self.state = StateManager()

    # -------------------------------------------------
    # MAIN EXECUTION ENTRY POINT
    # -------------------------------------------------
    async def execute(self, query: str, user_id: int | None = None):

        execution_context = {
            "query": query,
            "user_id": user_id,
            "tools_used": []
        }

        # -------------------------------------------------
        # 🔌 EXECUTION START EVENT
        # -------------------------------------------------
        self.state.emit_event(SystemEvent(
            type=EventType.TOOL_EXECUTED,  # placeholder-safe (no new enum assumption)
            payload={
                "stage": "execution_start",
                "query": query,
                "user_id": user_id
            },
            source="AIExecutor"
        ))

        try:
            # -------------------------------------------------
            # STEP 1: INTENT CLASSIFICATION
            # -------------------------------------------------
            intent = await self.intent_classification(query)

            # -------------------------------------------------
            # STEP 2: PLAN GRAPH
            # -------------------------------------------------
            graph = await self.build_graph(intent, query)

            # -------------------------------------------------
            # STEP 3: EXECUTE GRAPH
            # -------------------------------------------------
            tool_results = await self.run_graph(graph, execution_context)

            execution_context["tools_used"] = [
                t.get("tool") if isinstance(t, dict) else str(t)
                for t in tool_results or []
            ]

            # -------------------------------------------------
            # 🔌 TOOL EXECUTION EVENTS
            # -------------------------------------------------
            for tool in tool_results or []:
                self.state.emit_event(SystemEvent(
                    type=EventType.TOOL_EXECUTED,
                    payload={
                        "tool": tool.get("tool") if isinstance(tool, dict) else str(tool),
                        "result": str(tool)[:500]
                    },
                    source="AIExecutor"
                ))

            # -------------------------------------------------
            # STEP 4: RESPONSE BUILDING
            # -------------------------------------------------
            response = await self.build_response(
                query=query,
                intent=intent,
                tool_results=tool_results
            )

            # -------------------------------------------------
            # STEP 5: MEMORY / FINALIZATION (if exists in your system)
            # -------------------------------------------------
            if hasattr(self, "store_memory"):
                await self.store_memory(query, response, user_id)

            # -------------------------------------------------
            # 🔌 EXECUTION COMPLETED EVENT
            # -------------------------------------------------
            self.state.emit_event(SystemEvent(
                type=EventType.EXECUTION_COMPLETED,
                payload={
                    "query": query,
                    "user_id": user_id,
                    "response": str(response)[:1000],
                    "tools_used": execution_context["tools_used"],
                    "status": "success"
                },
                source="AIExecutor"
            ))

            return response

        except Exception as e:

            # -------------------------------------------------
            # ERROR STATE EVENT
            # -------------------------------------------------
            self.state.emit_event(SystemEvent(
                type=EventType.EXECUTION_COMPLETED,
                payload={
                    "query": query,
                    "user_id": user_id,
                    "error": str(e),
                    "status": "failed"
                },
                source="AIExecutor"
            ))

            raise

    # -------------------------------------------------
    # PLACEHOLDER METHODS (NO ASSUMPTION ABOUT YOUR CODE)
    # -------------------------------------------------
    async def intent_classification(self, query: str):
        raise NotImplementedError

    async def build_graph(self, intent, query: str):
        raise NotImplementedError

    async def run_graph(self, graph, context: dict):
        raise NotImplementedError

    async def build_response(self, query: str, intent, tool_results):
        raise NotImplementedError