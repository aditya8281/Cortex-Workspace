from backend.app.executor.schemas import (
    ExecutionPlan,
    IntentType,
    IntentDecision,
)

from backend.app.executor.graph import ExecutionGraph, ExecutionStep


class Planner:

    # -------------------------------------------------
    # LEGACY PATH (DO NOT REMOVE YET)
    # -------------------------------------------------
    def build_plan(self, intent):

        if isinstance(intent, IntentDecision):

            tools = []

            if intent.intent == IntentType.TOOL:
                if intent.subtype == "file_search":
                    tools.append("file_search")

            elif intent.intent == IntentType.SYSTEM:
                if intent.subtype == "system_scan":
                    tools.append("system_scanner")

            elif intent.intent == IntentType.RAG:
                if intent.subtype == "repo_rag":
                    tools.append("rag")

            return ExecutionPlan(
                intent=intent.intent,
                use_memory=True,
                use_llm=True,
                tools=tools
            )

        if intent == IntentType.TOOL:
            return ExecutionPlan(
                intent=intent,
                use_memory=True,
                use_llm=True,
                tools=["file_search"]
            )

        if intent == IntentType.SYSTEM:
            return ExecutionPlan(
                intent=intent,
                use_memory=True,
                use_llm=True,
                tools=["system_scanner"]
            )

        if intent == IntentType.RAG:
            return ExecutionPlan(
                intent=intent,
                use_memory=True,
                use_llm=True,
                tools=["rag"]
            )

        return ExecutionPlan(
            intent=IntentType.CHAT,
            use_memory=True,
            use_llm=True,
            tools=[]
        )

    # -------------------------------------------------
    # NEW: GRAPH BUILDER (CORTEX AGENT CORE START)
    # -------------------------------------------------
    def build_graph(self, intent) -> ExecutionGraph:

        graph = ExecutionGraph()

        # MEMORY STEP (always first if needed later)
        graph.add_step(
            ExecutionStep(
                id="memory_step",
                type="memory",
                name="memory_recall",
                input=None
            )
        )

        # TOOL STEP(S)
        tools = []

        if isinstance(intent, IntentDecision):
            intent_type = intent.intent
            subtype = intent.subtype

            if intent_type == IntentType.TOOL and subtype == "file_search":
                tools.append("file_search")

            elif intent_type == IntentType.SYSTEM and subtype == "system_scan":
                tools.append("system_scanner")

            elif intent_type == IntentType.RAG and subtype == "repo_rag":
                tools.append("rag")

        else:
            # legacy fallback
            if intent == IntentType.TOOL:
                tools.append("file_search")
            elif intent == IntentType.SYSTEM:
                tools.append("system_scanner")
            elif intent == IntentType.RAG:
                tools.append("rag")

        for i, tool in enumerate(tools):
            graph.add_step(
                ExecutionStep(
                    id=f"tool_step_{i}",
                    type="tool",
                    name=tool,
                    input=None,
                    depends_on=["memory_step"]
                )
            )

        # LLM STEP (final synthesis)
        graph.add_step(
            ExecutionStep(
                id="llm_step",
                type="llm",
                name="final_response",
                depends_on=[f"tool_step_{i}" for i in range(len(tools))]
            )
        )

        return graph