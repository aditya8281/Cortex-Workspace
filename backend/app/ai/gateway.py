from backend.app.executor import AIExecutor
from backend.app.executor.schemas import ExecutionResult


class AIGateway:

    def __init__(self):
        self.executor = AIExecutor()

    async def route(
        self,
        query: str,
        user_id: int | None = None,
        history: list = None
    ) -> ExecutionResult:

        result = await self.executor.execute(
            query=query,
            user_id=user_id,
            history=history
        )

        return result