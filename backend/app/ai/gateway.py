from backend.app.executor import AIExecutor
from backend.app.executor.schemas import ExecutionResult


class AIGateway:

    def __init__(self):
        self.executor = AIExecutor()

    async def route(
        self,
        query: str,
        user_id: int | None = None,
        history: list = None,
        llm_model: str | None = None,
        inference_engine: str | None = None,
        api_key: str | None = None,
        api_base_url: str | None = None,
        context_items: list = None
    ) -> ExecutionResult:

        result = await self.executor.execute(
            query=query,
            user_id=user_id,
            history=history,
            llm_model=llm_model,
            inference_engine=inference_engine,
            api_key=api_key,
            api_base_url=api_base_url,
            context_items=context_items
        )

        return result