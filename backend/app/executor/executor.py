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

from backend.app.executor.tool_feedback import ToolFeedbackStore


logger = get_logger(__name__)


class AIExecutor:

    def __init__(self):

        # -------------------------------
        # CORE PIPELINE
        # -------------------------------
        self.classifier = IntentClassifier()
        self.planner = Planner()
        self.builder = ResponseBuilder()

        # -------------------------------
        # MODEL + MEMORY
        # -------------------------------
        self.llm = LLMRouter()
        self.memory = MemoryRepository()

        # -------------------------------
        # AGENTS (legacy / fallback)
        # -------------------------------
        self.file_agent = FileSearchAgent()
        self.system_agent = SystemScanner()
        self.rag = RAGService(str(PROJECT_ROOT))

        # -------------------------------
        # TOOL SYSTEM
        # -------------------------------
        self.tool_registry = ToolRegistry(self)

        # -------------------------------
        # OBSERVABILITY
        # -------------------------------
        self.tracer = ExecutionTracer()

        # -------------------------------
        # GRAPH ENGINE
        # -------------------------------
        self.graph_runner = GraphRunner(self)

        # -------------------------------
        # LEARNING LAYER (NEW)
        # -------------------------------
        self.tool_feedback = ToolFeedbackStore()

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
        # TOOL BIAS (ADAPTIVE SIGNAL - NEW)
        # -------------------------------------------------
        tool_bias = self.tool_feedback.get_tool_bias()

        # inject bias into planner if supported
        graph = self.planner.build_graph(intent, tool_bias=tool_bias)

        # (future hook: planner can use tool_bias later)

        logger.info(f"execution_graph_built steps={len(graph.steps)}")

        # -------------------------------------------------
        # RUN GRAPH
        # -------------------------------------------------
        raw_state = await self.graph_runner.run(
            graph=graph,
            query=query,
            user_id=user_id
        )

        # -------------------------------------------------
        # MAP GRAPH → CONTEXT
        # -------------------------------------------------
        ctx = self._build_execution_context(
            query=query,
            user_id=user_id,
            raw_state=raw_state
        )

        # -------------------------------------------------
        # LEARNING FEEDBACK (CRITICAL ADDITION)
        # -------------------------------------------------
        self.tool_feedback.log(
            query=query,
            tools=ctx.tool_results
        )

        logger.info("executor_finished")

        return self.builder.build(ctx)

    # -------------------------------------------------
    # CONTEXT MAPPING (SAFE + CLEAN)
    # -------------------------------------------------
    def _build_execution_context(
        self,
        query: str,
        user_id: int | None,
        raw_state: dict
    ) -> ExecutionContext:

        memory = raw_state.get("memory")
        tools = raw_state.get("tools", [])
        llm = raw_state.get("llm")

        return ExecutionContext(
            query=query,
            user_id=user_id,
            memory=memory,
            tool_results=tools,
            llm_response=llm
        )
