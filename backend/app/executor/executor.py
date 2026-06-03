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
from backend.app.state.manager import StateManager


logger = get_logger(__name__)


class AIExecutor:
    def __init__(self):
        self.state = StateManager()
        self.classifier = IntentClassifier()
        self.planner = Planner()
        self.builder = ResponseBuilder()
        self.llm = LLMRouter()
        self.memory = MemoryRepository()
        self.file_agent = FileSearchAgent()
        self.system_agent = SystemScanner()
        self.rag = RAGService(str(PROJECT_ROOT))
        self.tool_registry = ToolRegistry(self)
        self.tracer = ExecutionTracer()
        self.graph_runner = GraphRunner(self)
        self.tool_feedback = ToolFeedbackStore()

    async def execute(
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

        logger.info(f"executor_started user_id={user_id} query={query[:100]}")

        try:
            intent = self.classifier.classify(query)
            tool_bias = self.tool_feedback.get_tool_bias()
            graph = self.planner.build_graph(intent, tool_bias=tool_bias)

            logger.info(f"execution_graph_built steps={len(graph.steps)}")
            raw_state = await self.graph_runner.run(
                graph=graph,
                query=query,
                user_id=user_id,
                intent=intent,
                history=history,
                llm_model=llm_model,
                embedding_model=embedding_model,
                vector_db=vector_db,
                inference_engine=inference_engine,
                code_parsing=code_parsing
            )

            ctx = self._build_execution_context(
                query=query,
                user_id=user_id,
                raw_state=raw_state
            )

            if user_id is not None and ctx.llm_response:
                try:
                    self.memory.add(
                        user_id=user_id,
                        query=query,
                        response=str(ctx.llm_response)
                    )
                    self.state.emit_event(SystemEvent(
                        type=EventType.MEMORY_STORED,
                        payload={
                            "user_id": user_id,
                            "query": query,
                            "response": str(ctx.llm_response)[:100]
                        },
                        source="AIExecutor"
                    ), execution_id=raw_state.get("execution_id"))
                except Exception as mem_ex:
                    logger.error(f"Failed to store conversation memory: {mem_ex}")

            self.tool_feedback.log(
                query=query,
                tools=ctx.tool_results
            )

            self.state.update_state(
                lambda state: self._sync_runtime_state(
                    state,
                    query=query,
                    execution_id=raw_state.get("execution_id"),
                    tools=ctx.tool_results,
                )
            )

            self.state.snapshot()

            logger.info("executor_finished")
            return self.builder.build(ctx)

        except Exception as e:

            logger.exception("executor_failed")
            raise

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
            execution_id=raw_state.get("execution_id"),
            memory=memory,
            tool_results=tools,
            llm_response=llm
        )

    def _sync_runtime_state(self, state, query: str, execution_id: str | None, tools):
        state.ai.last_queries = [query, *state.ai.last_queries][:20]

        if execution_id:
            state.ai.last_execution_id = execution_id

        state.ai.recent_tools = [t.tool for t in tools if getattr(t, "tool", None)][:20]
