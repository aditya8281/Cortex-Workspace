from backend.app.ai.llm_router import LLMRouter
from backend.app.ai.intelligent_router import IntelligentRouter
from backend.app.ai.memory.repository import MemoryRepository
from backend.app.agent.file_search import FileSearchAgent
from backend.app.agent.system_scanner import SystemScanner
from backend.app.agent.orchestrator import OrchestratorAgent

from backend.app.executor.intent_classifier import IntentClassifier
from backend.app.executor.workflow import WorkflowGraphBuilder, WorkflowExecutionEngine, WorkflowPlanner
from backend.app.executor.response_builder import ResponseBuilder
from backend.app.executor.schemas import ExecutionResult

from backend.app.executor.tracer import ExecutionTracer

from backend.app.core.logging import get_logger
from backend.app.core.paths import PROJECT_ROOT

from backend.app.executor.tool_registry import ToolRegistry
from backend.app.executor.context import ExecutionContext
from backend.app.executor.context_resolver import ContextResolver

from backend.app.executor.tool_feedback import ToolFeedbackStore
from backend.app.state.manager import StateManager
from backend.app.state.models import SystemEvent, EventType


logger = get_logger(__name__)


class AIExecutor:
    def __init__(self):
        self.state = StateManager()
        self.classifier = IntentClassifier()
        self.planner = WorkflowPlanner()
        self.builder = ResponseBuilder()
        self.llm = LLMRouter()
        self.router = IntelligentRouter()
        self.memory = MemoryRepository()
        self.file_agent = FileSearchAgent()
        self.system_agent = SystemScanner()
        self.tool_registry = ToolRegistry(self)
        self.tracer = ExecutionTracer()
        self.graph_builder = WorkflowGraphBuilder(self.tool_registry)
        self.workflow_engine = WorkflowExecutionEngine(self)
        self.tool_feedback = ToolFeedbackStore()
        self.context_resolver = ContextResolver()
        self.orchestrator = OrchestratorAgent(self)

    async def execute(
        self,
        query: str,
        user_id: int | None = None,
        history: list = None,
        llm_model: str | None = None,
        inference_engine: str | None = None,
        api_key: str | None = None,
        api_base_url: str | None = None,
        context_items: list = None
    ) -> ExecutionResult:

        logger.info(f"executor_started user_id={user_id} query={query[:100]}")

        try:
            if context_items:
                context_items = await self.context_resolver.resolve(context_items)
                logger.info(f"context_resolved items={len(context_items)}")

            intent = self.classifier.classify(query)
            workflow_plan = self.planner.build_plan(query, intent=intent, available_tools=self.tool_registry.list_tools())
            graph = self.graph_builder.build(workflow_plan)

            logger.info(f"execution_graph_built steps={len(graph.nodes)}")
            raw_state = await self.workflow_engine.execute(
                query=query,
                graph=graph,
                user_id=user_id,
                intent=intent,
                history=history,
                llm_model=llm_model,
                inference_engine=inference_engine,
                api_key=api_key,
                api_base_url=api_base_url,
                context_items=context_items
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

        except Exception:

            logger.exception("executor_failed")
            raise

    def _build_execution_context(
        self,
        query: str,
        user_id: int | None,
        raw_state: dict
    ) -> ExecutionContext:

        memory = raw_state.get("memory")
        tools = raw_state.get("tool_results", [])
        llm = raw_state.get("final_response")
        routing_info = raw_state.get("routing_info")
        workflow_summary = raw_state.get("workflow_summary")
        workflow_state = raw_state.get("workflow_state") or {}

        return ExecutionContext(
            query=query,
            user_id=user_id,
            execution_id=raw_state.get("execution_id"),
            memory=memory,
            tool_results=tools,
            llm_response=llm,
            routing_info=routing_info,
            meta={
                "workflow_summary": workflow_summary,
                "executed_steps": workflow_summary.get("steps", []) if isinstance(workflow_summary, dict) else [],
                "tools_used": workflow_summary.get("tools_used", []) if isinstance(workflow_summary, dict) else [],
                "retrieved_files": workflow_summary.get("retrieved_files", []) if isinstance(workflow_summary, dict) else [],
                "partial_results": workflow_summary.get("partial_results", False) if isinstance(workflow_summary, dict) else False,
                "workflow_state": workflow_state,
            }
        )

    def _sync_runtime_state(self, state, query: str, execution_id: str | None, tools):
        state.ai.last_queries = [query, *state.ai.last_queries][:20]

        if execution_id:
            state.ai.last_execution_id = execution_id

        state.ai.recent_tools = [t.tool for t in tools if getattr(t, "tool", None)][:20]
