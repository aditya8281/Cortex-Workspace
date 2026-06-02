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

        # -------------------------------------------------
        # BUILD EXECUTION GRAPH
        # -------------------------------------------------
        graph = self.planner.build_graph(intent)

        # -------------------------------------------------
        # RUN GRAPH (RAW EXECUTION STATE)
        # -------------------------------------------------
        raw_state = await self.graph_runner.run(
            graph=graph,
            query=query,
            user_id=user_id
        )

        # -------------------------------------------------
        # MAP GRAPH → EXECUTION CONTEXT (IMPORTANT FIX)
        # -------------------------------------------------
        ctx = self._build_execution_context(
            query=query,
            user_id=user_id,
            raw_state=raw_state
        )

        logger.info("executor_finished")

        return self.builder.build(ctx)
    
    def _build_execution_context(
        self,
        query: str,
        user_id: int | None,
        raw_state: dict
    ) -> ExecutionContext:

        # MEMORY
        memory = raw_state.get("memory")

        # TOOL RESULTS (keep structured if possible)
        tools = []

        for tool in raw_state.get("tools", []):
            tools.append(tool)

        # LLM OUTPUT
        llm = raw_state.get("llm")

        return ExecutionContext(
            query=query,
            user_id=user_id,
            memory=memory,
            tool_results=tools,
            llm_response=llm
        )
