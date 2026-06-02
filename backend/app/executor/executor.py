from backend.app.ai.llm_router import LLMRouter
from backend.app.ai.memory.repository import MemoryRepository
from backend.app.agent.file_search import FileSearchAgent
from backend.app.agent.system_scanner import SystemScanner

from backend.app.executor.intent_classifier import IntentClassifier
from backend.app.executor.planner import Planner
from backend.app.executor.response_builder import ResponseBuilder
from backend.app.executor.schemas import ExecutionResult

from backend.app.executor.tracer import ExecutionTracer
from backend.app.executor.graph_runner import GraphRunner

from backend.app.rag.service import RAGService

from backend.app.core.logging import get_logger
from backend.app.core.paths import PROJECT_ROOT

from backend.app.executor.tool_registry import ToolRegistry
from backend.app.executor.context import ExecutionContext


logger = get_logger(__name__)


class AIExecutor:

    def __init__(self):
        # core NLP pipeline
        self.classifier = IntentClassifier()
        self.planner = Planner()
        self.builder = ResponseBuilder()

        # model + memory
        self.llm = LLMRouter()
        self.memory = MemoryRepository()

        # agents (kept for backward compatibility / future use)
        self.file_agent = FileSearchAgent()
        self.system_agent = SystemScanner()
        self.rag = RAGService(str(PROJECT_ROOT))

        # tool system (SINGLE SOURCE OF TRUTH)
        self.tool_registry = ToolRegistry(self)

        # execution observability
        self.tracer = ExecutionTracer()

        # graph engine
        self.graph_runner = GraphRunner(self)

    # -------------------------------------------------
    # MAIN ENTRY
    # -------------------------------------------------
    async def execute(
        self,
        query: str,
        user_id: int | None = None
    ) -> ExecutionResult:

        logger.info(
            f"executor_started user_id={user_id} query={query[:100]}"
        )

        # -------------------------------------------------
        # INTENT CLASSIFICATION
        # -------------------------------------------------
        intent = self.classifier.classify(query)

        logger.info(f"classified_intent={intent}")

        # -------------------------------------------------
        # BUILD EXECUTION GRAPH
        # -------------------------------------------------
        graph = self.planner.build_graph(intent)

        logger.info(f"execution_graph_built steps={len(graph.steps)}")

        # -------------------------------------------------
        # RUN GRAPH
        # -------------------------------------------------
        result = await self.graph_runner.run(
            graph=graph,
            query=query,
            user_id=user_id
        )

        # -------------------------------------------------
        # FINAL CONTEXT BUILD
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
