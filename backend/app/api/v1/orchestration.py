from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db, get_current_user
from backend.app.models.user import User
from backend.app.executor.executor import AIExecutor
from backend.app.schemas.context_item import ContextItem

router = APIRouter()


class RunTaskRequest(BaseModel):
    query: str
    history: Optional[List[Dict[str, str]]] = None
    context_items: Optional[List[ContextItem]] = None
    user_id: Optional[int] = None
    llm_model: Optional[str] = None
    embedding_model: Optional[str] = None
    vector_db: Optional[str] = None
    inference_engine: Optional[str] = None
    code_parsing: Optional[str] = None
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None


class ExecuteAgentRequest(BaseModel):
    agent_name: str
    query: str
    context: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = None
    llm_model: Optional[str] = None
    inference_engine: Optional[str] = None
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None


class RouteTaskRequest(BaseModel):
    query: str
    context: Optional[str] = None


@router.post("/run_task")
async def run_task(payload: RunTaskRequest, db: Session = Depends(get_db)):
    """
    Run a task through the complete multi-agent orchestration execution graph.
    """
    try:
        executor = AIExecutor()
        response_text = await executor.orchestrator.execute(
            query=payload.query,
            context=None,
            history=payload.history,
            user_id=payload.user_id,
            llm_model=payload.llm_model,
            embedding_model=payload.embedding_model,
            vector_db=payload.vector_db,
            inference_engine=payload.inference_engine,
            code_parsing=payload.code_parsing,
            api_key=payload.api_key,
            api_base_url=payload.api_base_url,
            context_items=payload.context_items,
        )

        trace = executor.orchestrator.last_trace or {}

        return {
            "query": payload.query,
            "response": response_text,
            "user_id": payload.user_id,
            "execution_id": None,
            "routing_info": trace,
            "workflow_summary": {},
            "executed_steps": [],
            "tools_used": [],
            "retrieved_files": [],
            "partial_results": False,
            "trace": trace,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute_agent")
async def execute_agent(payload: ExecuteAgentRequest):
    """
    Execute a specific agent by name directly with custom query/context.
    """
    try:
        executor = AIExecutor()
        agent = executor.orchestrator.registry.get(payload.agent_name)
        if not agent:
            raise HTTPException(
                status_code=404,
                detail=f"Agent '{payload.agent_name}' not found."
            )

        result_dict = await agent.execute(
            query=payload.query,
            context=payload.context,
            history=payload.history,
            llm_model=payload.llm_model,
            inference_engine=payload.inference_engine,
            api_key=payload.api_key,
            api_base_url=payload.api_base_url
        )

        return {
            "agent_name": payload.agent_name,
            "query": payload.query,
            "result": result_dict.get("result"),
            "confidence": result_dict.get("confidence", 0.0),
            "reasoning_summary": result_dict.get("reasoning_summary", "")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/route_task")
async def route_task(payload: RouteTaskRequest):
    """
    Simulate routing and return the best suited agent and confidence score.
    """
    try:
        executor = AIExecutor()
        best_agent, confidence_score = executor.orchestrator.registry.route_request(
            payload.query,
            payload.context
        )
        classified_task = executor.orchestrator.classify_task(
            payload.query,
            payload.context
        )
        return {
            "query": payload.query,
            "agent_selected": best_agent.name,
            "confidence": confidence_score,
            "classified_task": classified_task
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debug_execution_graph")
async def debug_execution_graph(query: Optional[str] = None):
    """
    Get the structural schema of the execution graph mapped to a query.
    """
    try:
        q = query or "Explain app architecture and codebase"
        executor = AIExecutor()
        
        # 1. Classify task and select base agent using orchestrator
        best_agent, confidence_score = executor.orchestrator.registry.route_request(q, None)
        task_class = executor.orchestrator.classify_task(q, None)
        
        # 2. Replicate Orchestrator graph building logic
        from backend.app.agent.orchestrator import OrchestrationGraph, OrchestrationNode
        graph = OrchestrationGraph(executor.orchestrator)
        if task_class in ["Coding", "Execution"]:
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

        # Format nodes to match what the test expects:
        nodes_list = []
        for node in graph.nodes.values():
            nodes_list.append({
                "id": node.id,
                "agent_name": node.agent_name,
                "depends_on": node.depends_on,
                "status": node.status.value if hasattr(node.status, "value") else str(node.status),
            })

        return {
            "query": q,
            "classified_task": task_class,
            "agent_selected": best_agent.name,
            "graph_structure": {
                "nodes": nodes_list,
                "layers": [],
                "edges": [],
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
