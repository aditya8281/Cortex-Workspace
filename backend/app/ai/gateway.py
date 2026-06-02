from backend.app.executor import AIExecutor


class AIGateway:

    def __init__(self):
        self.executor = AIExecutor()

    async def route(
        self,
        query: str,
        user_id: int | None = None
    ) -> str:

        result = await self.executor.execute(
            query=query,
            user_id=user_id
        )

        return result.answer