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
                tool_name="file_search"
            )

        if intent == IntentType.SYSTEM:
            return ExecutionPlan(
                intent=intent,
                tool_name="system_scanner"
            )

        return ExecutionPlan(
            intent=IntentType.CHAT
        )