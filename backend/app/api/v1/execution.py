from fastapi import APIRouter, HTTPException

from backend.app.executor.execution_replay import ExecutionReplayEngine

router = APIRouter()
replay_engine = ExecutionReplayEngine()


@router.get("")
async def list_executions(limit: int = 50):
    return replay_engine.list_executions(limit=limit)


@router.get("/{execution_id}")
async def get_execution(execution_id: str):
    data = replay_engine.load_execution(execution_id)

    if not data["exists"]:
        raise HTTPException(
            status_code=404,
            detail="Execution not found"
        )

    return data


@router.get("/{execution_id}/replay")
async def replay_execution(execution_id: str):
    data = replay_engine.load_execution(execution_id)

    if not data["exists"]:
        raise HTTPException(
            status_code=404,
            detail="Execution not found"
        )

    replay = replay_engine.replay_step_by_step(execution_id)

    return {
        "execution_id": execution_id,
        "status": data["status"],
        "summary": data["summary"],
        "replay": replay
    }


@router.get("/{execution_id}/tools")
async def tool_usage(execution_id: str):
    data = replay_engine.load_execution(execution_id)

    if not data["exists"]:
        raise HTTPException(
            status_code=404,
            detail="Execution not found"
        )

    return replay_engine.get_tool_usage(execution_id)
