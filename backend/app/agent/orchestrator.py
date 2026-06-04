import time
import asyncio
from typing import List, Dict, Any, Optional
from enum import Enum

from backend.app.agent.base import BaseAgent
from backend.app.agent.registry import AgentRegistry
from backend.app.agent.agents import (
    ChatAgent,
    SearchAgent,
    RepositoryAgent,
    CodingAgent,
    PlanningAgent,
    MemoryAgent,
    ExecutionAgent,
    ResearchAgent,
    VerificationAgent
)
from backend.app.core.logging import get_logger

logger = get_logger(__name__)


class NodeStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class OrchestrationNode:
    def __init__(self, node_id: str, agent_name: str, depends_on: List[str] = None):
        self.id = node_id
        self.agent_name = agent_name
        self.depends_on = depends_on or []
        self.status = NodeStatus.PENDING
        self.result = None
        self.start_time = None
        self.end_time = None
        self.execution_time = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "agent_name": self.agent_name,
            "depends_on": self.depends_on,
            "status": self.status.value,
            "execution_time": self.execution_time,
            "confidence": self.result.get("confidence", 1.0) if self.result else 0.0,
            "reasoning_summary": self.result.get("reasoning_summary", "") if self.result else "",
            "verified": self.result.get("verified") if self.result and "verified" in self.result else None,
            "issues": self.result.get("issues") if self.result and "issues" in self.result else []
        }


class OrchestrationGraph:
    def __init__(self, orchestrator: Any):
        self.orchestrator = orchestrator
        self.nodes: Dict[str, OrchestrationNode] = {}
        self.execution_order: List[str] = []

    def add_node(self, node: OrchestrationNode):
        self.nodes[node.id] = node

    async def execute(
        self,
        query: str,
        base_context: str,
        history: Optional[List[Dict[str, str]]],
        **kwargs: Any
    ) -> Dict[str, Any]:
        pending_nodes = list(self.nodes.values())
        completed_node_ids = set()

        while pending_nodes:
            ready_nodes = [
                n for n in pending_nodes
                if all(dep in completed_node_ids for dep in n.depends_on)
            ]

            if not ready_nodes:
                logger.error("OrchestrationGraph: cycle or deadlock detected in dependencies.")
                break

            tasks = [self._execute_node(n, query, base_context, history, **kwargs) for n in ready_nodes]
            results = await asyncio.gather(*tasks)

            for node, res in zip(ready_nodes, results):
                node.result = res
                node.status = NodeStatus.COMPLETED if res.get("result") else NodeStatus.FAILED
                completed_node_ids.add(node.id)
                self.execution_order.append(node.id)
                pending_nodes.remove(node)

        final_node_id = self.execution_order[-1] if self.execution_order else None
        final_node = self.nodes.get(final_node_id) if final_node_id else None
        
        answer_text = ""
        verification_results = {}
        
        if final_node and final_node.agent_name == "VerificationAgent":
            verification_results = {
                "verified": final_node.result.get("verified", True),
                "issues": final_node.result.get("issues", []),
                "report": final_node.result.get("result", "")
            }
            dep_node_id = final_node.depends_on[0] if final_node.depends_on else None
            dep_node = self.nodes.get(dep_node_id) if dep_node_id else None
            answer_text = dep_node.result.get("result", "") if dep_node else final_node.result.get("result", "")
        else:
            answer_text = final_node.result.get("result", "") if final_node else "No output from orchestration graph."

        return {
            "answer": answer_text,
            "verification_results": verification_results,
            "nodes_trace": [n.to_dict() for n in self.nodes.values()],
            "execution_order": self.execution_order
        }

    async def _execute_node(
        self,
        node: OrchestrationNode,
        query: str,
        base_context: str,
        history: Optional[List[Dict[str, str]]],
        **kwargs: Any
    ) -> Dict[str, Any]:
        node.status = NodeStatus.RUNNING
        node.start_time = time.time()

        agent = self.orchestrator.registry.get(node.agent_name)
        if not agent:
            node.status = NodeStatus.FAILED
            node.execution_time = 0.0
            return {"result": f"Agent {node.agent_name} not registered.", "confidence": 0.0, "reasoning_summary": "Failed to find agent."}

        local_context = base_context
        dep_outputs = []
        for dep_id in node.depends_on:
            dep_node = self.nodes[dep_id]
            if dep_node.result:
                dep_outputs.append(
                    f"=== Output from {dep_node.agent_name} ===\n"
                    f"{dep_node.result.get('result', '')}"
                )
        if dep_outputs:
            local_context += "\n\n" + "\n\n".join(dep_outputs)

        exec_kwargs = {**kwargs}
        if node.agent_name == "VerificationAgent":
            dep_node_id = node.depends_on[0] if node.depends_on else None
            dep_node = self.nodes.get(dep_node_id) if dep_node_id else None
            exec_kwargs["target_text"] = dep_node.result.get("result", query) if dep_node else query
            exec_kwargs["rag_context"] = base_context

        try:
            res = await agent.execute(
                query=query,
                context=local_context,
                history=history,
                **exec_kwargs
            )
            node.status = NodeStatus.COMPLETED
            node.end_time = time.time()
            node.execution_time = node.end_time - node.start_time
            return res
        except Exception as e:
            logger.error(f"OrchestrationGraph: Node {node.id} execution failed: {e}")
            node.status = NodeStatus.FAILED
            node.end_time = time.time()
            node.execution_time = node.end_time - node.start_time
            return {"result": f"Error: {e}", "confidence": 0.0, "reasoning_summary": f"Exception raised during execution: {e}"}


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
        self._cached_contexts: Dict[str, str] = {}

    async def build(
        self,
        query: str,
        history: Optional[List[Dict[str, str]]] = None,
        context_items: Optional[List[Any]] = None,
        user_id: Optional[int] = None
    ) -> str:
        import hashlib
        # Build stable cache key
        history_key = str(history) if history else ""
        items_key = ",".join(str(getattr(item, "id", item)) for item in context_items) if context_items else ""
        cache_key = hashlib.md5(f"{query}||{history_key}||{items_key}||{user_id}".encode("utf-8")).hexdigest()

        if cache_key in self._cached_contexts:
            logger.info("ContextBuilder: context cache HIT")
            return self._cached_contexts[cache_key]

        from backend.app.services.hierarchical_rag import HierarchicalRAGService
        from backend.app.db.session import SessionLocal

        db = SessionLocal()
        try:
            rag_service = HierarchicalRAGService(executor=self.executor)
            compiled_context = await rag_service.build_context(
                query=query,
                db=db,
                context_items=context_items,
                history=history,
                user_id=user_id
            )
            self._cached_contexts[cache_key] = compiled_context
            return compiled_context
        except Exception as e:
            logger.error(f"ContextBuilder: Hierarchical RAG context builder failed: {e}")
            return f"Query: {query}"
        finally:
            db.close()


class OrchestratorAgent(BaseAgent):
    name = "OrchestratorAgent"
    description = "Classifies user intent, selects collaboration route, builds execution graph, and tracks trace metadata."
    capabilities = ["orchestration"]

    def __init__(self, executor: Any):
        self.executor = executor
        self.registry = AgentRegistry()
        self.context_builder = ContextBuilder(executor)
        self.last_trace: Dict[str, Any] = {}

        # Register default subagents
        self.registry.register(ChatAgent(executor))
        self.registry.register(SearchAgent(executor))
        self.registry.register(RepositoryAgent(executor))
        self.registry.register(CodingAgent(executor))
        self.registry.register(PlanningAgent(executor))
        self.registry.register(MemoryAgent(executor))
        self.registry.register(ExecutionAgent(executor))
        self.registry.register(ResearchAgent(executor))
        self.registry.register(VerificationAgent(executor))

    def confidence(self, query: str, context: Optional[str] = None) -> float:
        return 1.0

    def classify_task(self, query: str, context: Optional[str] = None) -> str:
        agent, score = self.registry.route_request(query, context)
        mapping = {
            "ChatAgent": "Chat",
            "SearchAgent": "Search",
            "RepositoryAgent": "Repository Analysis",
            "CodingAgent": "Coding",
            "PlanningAgent": "Planning",
            "MemoryAgent": "Memory Retrieval",
            "ExecutionAgent": "Execution",
            "ResearchAgent": "Research",
            "VerificationAgent": "Verification"
        }
        return mapping.get(agent.name, "Chat")

    def build_execution_graph(self, task_class: str) -> OrchestrationGraph:
        """
        Build the orchestration graph without executing it.
        Useful for debug/introspection endpoints and tests.
        """
        graph = OrchestrationGraph(self)

        if task_class in ["Coding", "Execution", "Repository Analysis"]:
            graph.add_node(OrchestrationNode("RepositoryAgent", "RepositoryAgent"))
            graph.add_node(OrchestrationNode("SearchAgent", "SearchAgent"))

            primary_agent_name = "ExecutionAgent" if task_class == "Execution" else "CodingAgent"
            graph.add_node(OrchestrationNode(primary_agent_name, primary_agent_name, ["RepositoryAgent", "SearchAgent"]))
            graph.add_node(OrchestrationNode("VerificationAgent", "VerificationAgent", [primary_agent_name]))

        elif task_class in ["Search", "Research"]:
            primary_agent_name = "SearchAgent" if task_class == "Search" else "ResearchAgent"
            graph.add_node(OrchestrationNode(primary_agent_name, primary_agent_name))
            graph.add_node(OrchestrationNode("VerificationAgent", "VerificationAgent", [primary_agent_name]))

        elif task_class == "Planning":
            graph.add_node(OrchestrationNode("PlanningAgent", "PlanningAgent"))
            graph.add_node(OrchestrationNode("VerificationAgent", "VerificationAgent", ["PlanningAgent"]))

        elif task_class == "Memory Retrieval":
            graph.add_node(OrchestrationNode("MemoryAgent", "MemoryAgent"))

        else:
            graph.add_node(OrchestrationNode("ChatAgent", "ChatAgent"))

        return graph

    def debug_execution_graph(self, query: str, context: Optional[str] = None) -> Dict[str, Any]:
        best_agent, confidence_score = self.registry.route_request(query, context)
        task_class = self.classify_task(query, context)
        graph = self.build_execution_graph(task_class)

        return {
            "query": query,
            "agent_selected": best_agent.name,
            "confidence": confidence_score,
            "classified_task": task_class,
            "graph_structure": {
                "nodes": [node.to_dict() for node in graph.nodes.values()],
                "execution_order": graph.execution_order,
            },
        }

    async def execute(
        self,
        query: str,
        context: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        **kwargs: Any
    ) -> str:
        start_time = time.time()
        
        # 1. Classify task and select base agent
        best_agent, confidence_score = self.registry.route_request(query, context)
        task_class = self.classify_task(query, context)
        
        reason = f"Routed to {best_agent.name} ({task_class}) with confidence score of {confidence_score:.2f}"
        logger.info(f"orchestrator_selected_agent={best_agent.name} confidence={confidence_score:.2f} reason={reason}")

        # 2. Build base context using ContextBuilder
        user_id = kwargs.get("user_id")
        context_items = kwargs.get("context_items")
        assembled_context = await self.context_builder.build(
            query=query,
            history=history,
            context_items=context_items,
            user_id=user_id
        )

        # 3. Construct OrchestrationGraph
        graph = OrchestrationGraph(self)
        
        if task_class in ["Coding", "Execution", "Repository Analysis"]:
            graph.add_node(OrchestrationNode("RepositoryAgent", "RepositoryAgent"))
            graph.add_node(OrchestrationNode("SearchAgent", "SearchAgent"))
            
            primary_agent_name = "ExecutionAgent" if task_class == "Execution" else "CodingAgent"
            graph.add_node(OrchestrationNode(primary_agent_name, primary_agent_name, ["RepositoryAgent", "SearchAgent"]))
            graph.add_node(OrchestrationNode("VerificationAgent", "VerificationAgent", [primary_agent_name]))
            
        elif task_class in ["Search", "Research"]:
            primary_agent_name = "SearchAgent" if task_class == "Search" else "ResearchAgent"
            graph.add_node(OrchestrationNode(primary_agent_name, primary_agent_name))
            graph.add_node(OrchestrationNode("VerificationAgent", "VerificationAgent", [primary_agent_name]))
            
        elif task_class == "Planning":
            graph.add_node(OrchestrationNode("PlanningAgent", "PlanningAgent"))
            graph.add_node(OrchestrationNode("VerificationAgent", "VerificationAgent", ["PlanningAgent"]))
            
        elif task_class == "Memory Retrieval":
            graph.add_node(OrchestrationNode("MemoryAgent", "MemoryAgent"))
            
        else:  # Chat / Fallback
            graph.add_node(OrchestrationNode("ChatAgent", "ChatAgent"))

        # 4. Execute orchestration graph
        graph_result = await graph.execute(
            query=query,
            base_context=assembled_context,
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
            "classified_task": task_class,
            "execution_order": graph_result["execution_order"],
            "collaboration_graph": graph_result["nodes_trace"],
            "verification_results": graph_result["verification_results"]
        }

        return graph_result["answer"]
