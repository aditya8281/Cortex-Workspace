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
        result = await executor.execute(
            query=payload.query,
            user_id=payload.user_id,
            history=payload.history,
            llm_model=payload.llm_model,
            embedding_model=payload.embedding_model,
            vector_db=payload.vector_db,
            inference_engine=payload.inference_engine,
            code_parsing=payload.code_parsing,
            api_key=payload.api_key,
            api_base_url=payload.api_base_url,
            context_items=payload.context_items
        )

        workflow_trace = executor.tracer.get_session(result.execution_id) if result.execution_id else None

        return {
            "query": payload.query,
            "response": result.answer,
            "user_id": payload.user_id,
            "execution_id": result.execution_id,
            "routing_info": result.routing_info,
            "workflow_summary": result.workflow_summary,
            "executed_steps": result.executed_steps,
            "tools_used": result.tools_used,
            "retrieved_files": result.retrieved_files,
            "partial_results": result.partial_results,
            "trace": workflow_trace or {},
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
        intent = executor.classifier.classify(q)
        plan = executor.planner.build_plan(q, intent=intent, available_tools=executor.tool_registry.list_tools())
        graph = executor.graph_builder.build(plan)

        return {
            "query": q,
            "classified_task": intent.intent.value if hasattr(intent.intent, "value") else str(intent.intent),
            "plan": plan.model_dump(),
            "graph_structure": {
                "nodes": [
                    {
                        "id": node.id,
                        "step_id": node.step_id,
                        "tool": node.tool,
                        "depends_on": node.depends_on,
                        "fallback_tools": node.fallback_tools,
                        "critical": node.critical,
                        "description": node.description,
                    }
                    for node in graph.nodes
                ],
                "layers": graph.layers,
                "edges": graph.edges,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
