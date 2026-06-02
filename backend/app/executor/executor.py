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

        intent = self.classifier.classify(query)

        plan = self.planner.build_plan(intent)

        if plan.use_memory and user_id:

            memory = self.memory.search(
                user_id=user_id,
                query=query
            )

            if memory:
                return self.builder.build(
                    answer=memory,
                    source="memory",
                    memory_used=True
                )

        if plan.tool_name == "file_search":

            result = self.file_agent.search(query)

            return self.builder.build(
                answer=result,
                source="file_search"
            )

        if plan.tool_name == "system_scanner":

            result = self.system_agent.scan(query)

            return self.builder.build(
                answer=result,
                source="system_scanner"
            )

        response = await self.llm.generate(query)

        if user_id:
            self.memory.add(
                user_id=user_id,
                query=query,
                response=response
            )

        return self.builder.build(
            answer=response,
            source="llm"
        )