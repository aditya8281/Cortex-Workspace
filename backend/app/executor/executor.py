from backend.app.ai.llm_router import LLMRouter
from backend.app.ai.memory.repository import MemoryRepository
from backend.app.agent.file_search import FileSearchAgent
from backend.app.agent.system_scanner import SystemScanner

from backend.app.executor.intent_classifier import IntentClassifier
from backend.app.executor.planner import Planner
from backend.app.executor.response_builder import ResponseBuilder
from backend.app.executor.schemas import ExecutionResult, IntentDecision

from backend.app.executor.graph_runner import GraphRunner

from backend.app.rag.service import RAGService

from backend.app.core.logging import get_logger
from backend.app.core.paths import PROJECT_ROOT

logger = get_logger(__name__)


class AIExecutor:

    def __init__(self):
        self.classifier = IntentClassifier()
        self.planner = Planner()
        self.builder = ResponseBuilder()

        self.llm = LLMRouter()
        self.memory = MemoryRepository()

        self.file_agent = FileSearchAgent()
        self.system_agent = SystemScanner()

        self.rag = RAGService(str(PROJECT_ROOT))

        # Graph runtime engine
        self.graph_runner = GraphRunner(self)

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

        logger.info(
            f"executor_started user_id={user_id} query={query[:100]}"
        )

        # -------------------------------------------------
        # INTENT CLASSIFICATION
        # -------------------------------------------------
        intent = self.classifier.classify(query)

        logger.info(
            f"classified_intent={intent}"
        )

        # -------------------------------------------------
        # GRAPH BUILDING (CORE UPGRADE)
        # -------------------------------------------------
        graph = self.planner.build_graph(intent)

        logger.info(
            f"execution_graph_built steps={len(graph.steps)}"
        )

        # -------------------------------------------------
        # GRAPH EXECUTION
        # -------------------------------------------------
        result = await self.graph_runner.run(
            graph=graph,
            query=query,
            user_id=user_id
        )

        # -------------------------------------------------
        # BUILD FINAL CONTEXT
        # -------------------------------------------------
        ctx = ExecutionContext(
            query=query,
            user_id=user_id,
            memory=result.get("memory"),
            tool_results=result.get("tools", []),
            llm_response=result.get("llm")
        )

        logger.info("executor_finished")

        return self.builder.build(ctx)