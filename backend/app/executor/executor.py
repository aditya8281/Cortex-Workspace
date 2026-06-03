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

# -------------------------------
# STATE LAYER (NEW)
# -------------------------------
from backend.app.state.manager import StateManager
from backend.app.state.models import SystemEvent, EventType


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
        # OBSERVABILITY (legacy)
        # -------------------------------
        self.tracer = ExecutionTracer()

        # -------------------------------
        # GRAPH ENGINE
        # -------------------------------
        self.graph_runner = GraphRunner(self)

        # -------------------------------
        # LEARNING LAYER
        # -------------------------------
        self.tool_feedback = ToolFeedbackStore()

        # -------------------------------
        # SYSTEM STATE (NEW)
        # -------------------------------
        self.state = StateManager()

    # -------------------------------------------------
    # MAIN ENTRY
    # -------------------------------------------------
    async def execute(
        self,
        query: str,
        user_id: int | None = None
    ) -> ExecutionResult:

        logger.info(f"executor_started user_id={user_id} query={query[:100]}")

        # -------------------------------
        # STATE: EXECUTION START
        # -------------------------------
        self.state.emit_event(SystemEvent(
            type=EventType.TOOL_EXECUTED,
            payload={
                "stage": "execution_start",
                "query": query,
                "user_id": user_id
            },
            source="AIExecutor"
        ))

        try:

            # -------------------------------------------------
            # INTENT CLASSIFICATION
            # -------------------------------------------------
            intent = self.classifier.classify(query)

            # -------------------------------------------------
            # TOOL BIAS (ADAPTIVE SIGNAL)
            # -------------------------------------------------
            tool_bias = self.tool_feedback.get_tool_bias()

            # -------------------------------------------------
            # PLAN GRAPH
            # -------------------------------------------------
            graph = self.planner.build_graph(intent, tool_bias=tool_bias)

            logger.info(f"execution_graph_built steps={len(graph.steps)}")

            # -------------------------------
            # STATE: GRAPH BUILT
            # -------------------------------
            self.state.emit_event(SystemEvent(
                type=EventType.TOOL_EXECUTED,
                payload={
                    "stage": "graph_built",
                    "steps": len(graph.steps),
                    "query": query
                },
                source="Planner"
            ))

            # -------------------------------------------------
            # RUN GRAPH
            # -------------------------------------------------
            raw_state = await self.graph_runner.run(
                graph=graph,
                query=query,
                user_id=user_id
            )

            # -------------------------------
            # STATE: TOOL EXECUTION EVENTS
            # -------------------------------
            for tool in raw_state.get("tools", []):
                self.state.emit_event(SystemEvent(
                    type=EventType.TOOL_EXECUTED,
                    payload={
                        "tool": tool.get("tool") if isinstance(tool, dict) else str(tool),
                        "result_preview": str(tool)[:300]
                    },
                    source="GraphRunner"
                ))

            # -------------------------------------------------
            # BUILD CONTEXT
            # -------------------------------------------------
            ctx = self._build_execution_context(
                query=query,
                user_id=user_id,
                raw_state=raw_state
            )

            # -------------------------------
            # STATE: CONTEXT BUILT / MEMORY SIGNAL
            # -------------------------------
            self.state.emit_event(SystemEvent(
                type=EventType.MEMORY_STORED,
                payload={
                    "query": query,
                    "has_memory": ctx.memory is not None,
                    "tool_count": len(ctx.tool_results or [])
                },
                source="ContextBuilder"
            ))

            # -------------------------------------------------
            # LEARNING FEEDBACK
            # -------------------------------------------------
            self.tool_feedback.log(
                query=query,
                tools=ctx.tool_results
            )

            logger.info("executor_finished")

            # -------------------------------
            # STATE: EXECUTION COMPLETE
            # -------------------------------
            self.state.emit_event(SystemEvent(
                type=EventType.EXECUTION_COMPLETED,
                payload={
                    "query": query,
                    "user_id": user_id,
                    "tool_count": len(ctx.tool_results or []),
                    "status": "success"
                },
                source="AIExecutor"
            ))

            return self.builder.build(ctx)

        except Exception as e:

            logger.exception("executor_failed")

            # -------------------------------
            # STATE: EXECUTION FAILED
            # -------------------------------
            self.state.emit_event(SystemEvent(
                type=EventType.EXECUTION_COMPLETED,
                payload={
                    "query": query,
                    "user_id": user_id,
                    "status": "failed",
                    "error": str(e)
                },
                source="AIExecutor"
            ))

            raise

    # -------------------------------------------------
    # CONTEXT MAPPING
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