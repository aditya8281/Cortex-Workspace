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
        embedding_model: str | None = None,
        vector_db: str | None = None,
        inference_engine: str | None = None,
        code_parsing: str | None = None
    ) -> ExecutionResult:

        result = await self.executor.execute(
            query=query,
            user_id=user_id,
            history=history,
            llm_model=llm_model,
            embedding_model=embedding_model,
            vector_db=vector_db,
            inference_engine=inference_engine,
            code_parsing=code_parsing
        )

        return result