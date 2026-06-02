from backend.app.ai.llm_router import LLMRouter
from backend.app.ai.memory.repository import MemoryRepository
from backend.app.agent.file_search import FileSearchAgent
from backend.app.agent.system_scanner import SystemScanner

from backend.app.executor.intent_classifier import IntentClassifier
from backend.app.executor.planner import Planner
from backend.app.executor.response_builder import ResponseBuilder
from backend.app.executor.schemas import ExecutionResult


class AIExecutor:

    def __init__(self):
        self.classifier = IntentClassifier()
        self.planner = Planner()
        self.builder = ResponseBuilder()

        self.llm = LLMRouter()
        self.memory = MemoryRepository()

        self.file_agent = FileSearchAgent()
        self.system_agent = SystemScanner()

    async def execute(
        self,
        query: str,
        user_id: int | None = None
    ) -> ExecutionResult:

        from backend.app.executor.context import ExecutionContext

        ctx = ExecutionContext(
            query=query,
            user_id=user_id
        )

        intent = self.classifier.classify(query)

        plan = self.planner.build_plan(intent)

        if plan.use_memory and user_id:
            ctx.memory = self.memory.search(
                user_id=user_id,
                query=query
            )

        for tool in plan.tools:

            if tool == "file_search":

                result = self.file_agent.search(query)

                ctx.tool_results.append(result)

            elif tool == "system_scanner":

                result = self.system_agent.scan(query)

                ctx.tool_results.append(result)

        if plan.use_llm:

            prompt_parts = []

            if ctx.memory:
                prompt_parts.append(ctx.memory)

            prompt_parts.extend(ctx.tool_results)

            prompt_parts.append(query)

            final_prompt = "\n\n".join(prompt_parts)

            ctx.llm_response = await self.llm.generate(
                final_prompt
            )

            if user_id:
                self.memory.add(
                    user_id=user_id,
                    query=query,
                    response=ctx.llm_response
                )

        return self.builder.build(ctx)