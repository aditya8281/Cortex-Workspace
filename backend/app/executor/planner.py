from backend.app.executor.schemas import (
    ExecutionPlan,
    IntentType,
    IntentDecision,
)


class Planner:

    def build_plan(self, intent):

        # -------------------------------------------------
        # NEW SYSTEM PATH (IntentDecision)
        # -------------------------------------------------
        if isinstance(intent, IntentDecision):

            tools = []

            # TOOL INTENTS
            if intent.intent == IntentType.TOOL:

                if intent.subtype == "file_search":
                    tools.append("file_search")

            # SYSTEM INTENTS
            elif intent.intent == IntentType.SYSTEM:

                if intent.subtype == "system_scan":
                    tools.append("system_scanner")

            # RAG INTENTS
            elif intent.intent == IntentType.RAG:

                if intent.subtype == "repo_rag":
                    tools.append("rag")

            return ExecutionPlan(
                intent=intent.intent,
                use_memory=True,
                use_llm=True,
                tools=tools
            )

        # -------------------------------------------------
        # LEGACY SYSTEM PATH (IntentType fallback)
        # -------------------------------------------------

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