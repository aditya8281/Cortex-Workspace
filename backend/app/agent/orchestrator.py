import time
from typing import List, Dict, Any, Optional
from backend.app.agent.base import BaseAgent
from backend.app.agent.registry import AgentRegistry
from backend.app.agent.agents import (
    ChatAgent,
    SearchAgent,
    RepoAnalysisAgent,
    CodingAgent,
    PlanningAgent,
    MemoryRetrievalAgent,
    ExecutionAgent,
    ResearchAgent
)
from backend.app.core.logging import get_logger

logger = get_logger(__name__)


class ContextBuilder:
    """
    Context assembly pipeline with priority:
    1. Attached Context (explicitly attached files, folders, URLs, etc.)
    2. Workspace Context (repository profile overview)
    3. Conversation Context (recent message history)
    4. Memory Context (persistent memories matching keywords)
    5. Retrieval Context (RAG search chunks)
    """
    def __init__(self, executor: Any):
        self.executor = executor

    async def build(
        self,
        query: str,
        history: Optional[List[Dict[str, str]]] = None,
        context_items: Optional[List[Any]] = None,
        user_id: Optional[int] = None
    ) -> str:
        blocks = []

        # 1. Attached Context (Highest priority)
        if context_items:
            from backend.app.executor.context_compiler import ContextCompiler
            compiler = ContextCompiler()
            attached_block = compiler._format_context_items(context_items)
            if attached_block:
                blocks.append(attached_block)

        # 2. Workspace Context
        from backend.app.db.session import SessionLocal
        from backend.app.intelligence.models import RepositoryProfile
        db = SessionLocal()
        try:
            profile = db.query(RepositoryProfile).order_by(RepositoryProfile.updated_at.desc()).first()
            if profile:
                blocks.append(
                    f"=== Workspace Context ===\n"
                    f"Project: {profile.name}\n"
                    f"Tech Stack: {profile.tech_stack}\n"
                    f"Architecture Overview: {profile.architecture_summary}\n"
                    f"=== End of Workspace Context ==="
                )
        except Exception as e:
            logger.warning(f"ContextBuilder failed to fetch workspace profile: {e}")
        finally:
            db.close()

        # 3. Conversation Context
        if history:
            history_str = "=== Conversation History ===\n"
            for turn in history:
                role = turn.get("role", "user")
                content = turn.get("content", "")
                role_display = "User" if role == "user" else "Assistant"
                history_str += f"{role_display}: {content}\n"
            history_str += "=== End of Conversation History ==="
            blocks.append(history_str)

        # 4. Memory Context
        from backend.app.intelligence.memory_service import PersistentMemoryService
        db = SessionLocal()
        try:
            memories = PersistentMemoryService().search(db, query, limit=3, user_id=user_id)
            if memories:
                mem_str = "=== Memory Context ===\n"
                for m in memories:
                    mem_str += f"- {m['title']}: {m['content'][:300]}\n"
                mem_str += "=== End of Memory Context ==="
                blocks.append(mem_str)
        except Exception as e:
            logger.warning(f"ContextBuilder failed to search memory: {e}")
        finally:
            db.close()

        # 5. Retrieval Context (RAG)
        try:
            rag_results = await self.executor.rag.search(query, top_k=3)
            if rag_results:
                rag_str = "=== Retrieval Context (RAG) ===\n"
                for idx, r in enumerate(rag_results):
                    chunk_text = r["data"]["chunk"] if isinstance(r, dict) and "data" in r else str(r)
                    rag_str += f"Chunk {idx+1}:\n{chunk_text[:500]}\n---\n"
                rag_str += "=== End of Retrieval Context ==="
                blocks.append(rag_str)
        except Exception as e:
            logger.warning(f"ContextBuilder failed RAG search: {e}")

        return "\n\n".join(blocks)


class OrchestratorAgent(BaseAgent):
    name = "OrchestratorAgent"
    description = "Classifies user intent, selects the best agent, assembles context, and tracks execution trace."
    capabilities = ["orchestration"]

    def __init__(self, executor: Any):
        self.executor = executor
        self.registry = AgentRegistry()
        self.context_builder = ContextBuilder(executor)
        self.last_trace: Dict[str, Any] = {}

        # Register default subagents
        self.registry.register(ChatAgent(executor))
        self.registry.register(SearchAgent(executor))
        self.registry.register(RepoAnalysisAgent(executor))
        self.registry.register(CodingAgent(executor))
        self.registry.register(PlanningAgent(executor))
        self.registry.register(MemoryRetrievalAgent(executor))
        self.registry.register(ExecutionAgent(executor))
        self.registry.register(ResearchAgent(executor))

    def confidence(self, query: str, context: Optional[str] = None) -> float:
        return 1.0  # Orchestrator handles all entries

    def classify_task(self, query: str, context: Optional[str] = None) -> str:
        """Helper to classify query into task types by checking confidence scores."""
        agent, score = self.registry.route_request(query, context)
        # Map agent name to classification task
        mapping = {
            "ChatAgent": "Chat",
            "SearchAgent": "Search",
            "RepoAnalysisAgent": "Repository Analysis",
            "CodingAgent": "Coding",
            "PlanningAgent": "Planning",
            "MemoryRetrievalAgent": "Memory Retrieval",
            "ExecutionAgent": "Execution",
            "ResearchAgent": "Research"
        }
        return mapping.get(agent.name, "Chat")

    async def execute(
        self,
        query: str,
        context: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        **kwargs: Any
    ) -> str:
        start_time = time.time()
        
        # 1. Select agent based on routing
        best_agent, confidence_score = self.registry.route_request(query, context)
        task_class = self.classify_task(query, context)
        
        reason = f"Routed to {best_agent.name} ({task_class}) with confidence score of {confidence_score:.2f}"
        logger.info(f"orchestrator_selected_agent={best_agent.name} confidence={confidence_score:.2f} reason={reason}")

        # 2. Build shared context using ContextBuilder pipeline
        user_id = kwargs.get("user_id")
        context_items = kwargs.get("context_items")
        assembled_context = await self.context_builder.build(
            query=query,
            history=history,
            context_items=context_items,
            user_id=user_id
        )

        # 3. Execute chosen agent
        response_text = await best_agent.execute(
            query=query,
            context=assembled_context,
            history=history,
            **kwargs
        )

        duration = time.time() - start_time

        # Save trace metadata
        self.last_trace = {
            "agent_selected": best_agent.name,
            "agent_confidence": confidence_score,
            "agent_execution_time": duration,
            "agent_reason": reason,
            "classified_task": task_class
        }

        return response_text
