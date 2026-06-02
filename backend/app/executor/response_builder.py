from backend.app.executor.schemas import ExecutionResult


class ResponseBuilder:

    def build(
        self,
        answer: str,
        source: str,
        memory_used: bool = False
    ) -> ExecutionResult:

        return ExecutionResult(
            answer=answer,
            source=source,
            memory_used=memory_used
        )