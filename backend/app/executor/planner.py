from backend.app.executor.schemas import (
    ExecutionPlan,
    IntentType,
    IntentDecision,
)

from backend.app.executor.graph import ExecutionGraph, ExecutionStep


class Planner:

    # -------------------------------------------------
    # LEGACY PATH (UNCHANGED)
    # -------------------------------------------------
    def build_plan(self, intent):

        tool_candidates = []
        tools = []

        if isinstance(intent, IntentDecision):

            if intent.intent == IntentType.TOOL:
                if intent.subtype == "file_search":
                    tools.append("file_search")
                    tool_candidates.append("file_search")

            elif intent.intent == IntentType.SYSTEM:
                if intent.subtype == "system_scan":
                    tools.append("system_scanner")
                    tool_candidates.append("system_scanner")

            elif intent.intent == IntentType.RAG:
                if intent.subtype == "repo_rag":
                    tools.append("rag")
                    tool_candidates.append("rag")

            return ExecutionPlan(
                intent=intent.intent,
                use_memory=True,
                use_llm=True,
                tools=tools,
                tool_candidates=tool_candidates
            )

        # fallback
        if intent == IntentType.TOOL:
            return ExecutionPlan(
                intent=intent,
                use_memory=True,
                use_llm=True,
                tools=["file_search"],
                tool_candidates=["file_search"]
            )

        if intent == IntentType.SYSTEM:
            return ExecutionPlan(
                intent=intent,
                use_memory=True,
                use_llm=True,
                tools=["system_scanner"],
                tool_candidates=["system_scanner"]
            )

        if intent == IntentType.RAG:
            return ExecutionPlan(
                intent=intent,
                use_memory=True,
                use_llm=True,
                tools=["rag"],
                tool_candidates=["rag"]
            )

        return ExecutionPlan(
            intent=IntentType.CHAT,
            use_memory=True,
            use_llm=True,
            tools=[],
            tool_candidates=[]
        )

    # -------------------------------------------------
    # GRAPH BUILDER (STABLE + TRACEABLE)
    # -------------------------------------------------
    def build_graph(self, intent) -> ExecutionGraph:

        graph = ExecutionGraph()

        # -----------------------------
        # MEMORY STEP
        # -----------------------------
        graph.add_step(
            ExecutionStep(
                id="memory_step",
                type="memory",
                name="memory_recall",
                depends_on=[]
            )
        )

        # -----------------------------
        # TOOL SELECTION
        # -----------------------------
        tools = self._resolve_tools(intent)

        tool_step_ids = []

        for tool_name in tools:

            step_id = f"tool_{tool_name}"

            graph.add_step(
                ExecutionStep(
                    id=step_id,
                    type="tool",
                    name=tool_name,
                    depends_on=["memory_step"]
                )
            )

            tool_step_ids.append(step_id)

        # -----------------------------
        # LLM STEP (FINAL SYNTHESIS)
        # -----------------------------
        graph.add_step(
            ExecutionStep(
                id="llm_step",
                type="llm",
                name="final_response",
                depends_on=[
                    "memory_step",
                    *tool_step_ids
                ]
            )
        )

        return graph

    # -------------------------------------------------
    # SINGLE SOURCE TOOL RESOLUTION LOGIC
    # -------------------------------------------------
    def _resolve_tools(self, intent):

        tools = []

        if isinstance(intent, IntentDecision):

            if intent.intent == IntentType.TOOL and intent.subtype == "file_search":
                tools.append("file_search")

            elif intent.intent == IntentType.SYSTEM and intent.subtype == "system_scan":
                tools.append("system_scanner")

            elif intent.intent == IntentType.RAG and intent.subtype == "repo_rag":
                tools.append("rag")

        else:
            if intent == IntentType.TOOL:
                tools.append("file_search")
            elif intent == IntentType.SYSTEM:
                tools.append("system_scanner")
            elif intent == IntentType.RAG:
                tools.append("rag")

        return tools