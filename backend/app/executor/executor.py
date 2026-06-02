from backend.app.ai.llm_router import LLMRouter
from backend.app.ai.memory.repository import MemoryRepository
from backend.app.agent.file_search import FileSearchAgent
from backend.app.agent.system_scanner import SystemScanner

from backend.app.executor.intent_classifier import IntentClassifier
from backend.app.executor.planner import Planner
from backend.app.executor.response_builder import ResponseBuilder
from backend.app.executor.schemas import ExecutionResult

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
            f"executor_started "
            f"user_id={user_id} "
            f"query={query[:100]}"
        )

        intent = self.classifier.classify(query)

        logger.info(
            f"classified_intent={intent}"
        )

        # -------------------------------------------------
        # COMPATIBILITY ADAPTER LAYER (CRITICAL)
        # -------------------------------------------------

        from backend.app.executor.schemas import IntentType, IntentDecision

        if isinstance(intent, IntentDecision):
            # New system path
            plan = self.planner.build_plan(intent)

        else:
            # Legacy fallback path (IntentType)
            plan = self.planner.build_plan(intent)

        plan = self.planner.build_plan(intent)

        logger.info(
            f"execution_plan={plan}"
        )

        if plan.use_memory and user_id is not None:
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
            
            elif tool == "rag":

                results = self.rag. search(
                    query
                )

                if results:

                    rag_context = "\n\n".join(
                        [
                            item["data"]["chunk"][:500]
                            for item in results
                        ]
                    )

                    ctx.tool_results.append(
                        f"Repository Context:\n{rag_context}"
                    )

            logger.info(    
                f"executing_tool={tool}"
            )

        if plan.use_llm:

            prompt_parts = []

            if ctx.memory:
                prompt_parts.append(ctx.memory)

            prompt_parts.extend(ctx.tool_results)

            prompt_parts.append(query)

            final_prompt = "\n\n".join(prompt_parts)

            logger.info(
                "calling_llm"
            )

            ctx.llm_response = await self.llm.generate(
                final_prompt
            )

            if user_id is not None:
                self.memory.add(
                    user_id=user_id,
                    query=query,
                    response=ctx.llm_response
                )

                
            logger.info(
                "executor_finished"
            )

            

        return self.builder.build(ctx)
