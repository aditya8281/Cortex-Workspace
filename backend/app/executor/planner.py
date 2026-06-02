from backend.app.executor.schemas import (
    ExecutionPlan,
    IntentType
)


class Planner:

    def build_plan(
        self,
        intent: IntentType
    ) -> ExecutionPlan:

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

        return ExecutionPlan(
            intent=IntentType.CHAT,
            use_memory=True,
            use_llm=True
        )