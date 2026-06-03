from fastapi import APIRouter, HTTPException
from backend.app.executor.execution_replay import ExecutionReplayEngine

router = APIRouter()

replay_engine = ExecutionReplayEngine()

# -------------------------------------------------
# FULL EXECUTION REPLAY
# -------------------------------------------------
@router.get("/execution/{execution_id}")
async def get_execution(execution_id: str):

    data = replay_engine.load_execution(execution_id)

    if data["status"] != "ok":
        raise HTTPException(
            status_code=404,
            detail="Execution not found"
        )

    return data


# -------------------------------------------------
# STEP-BY-STEP REPLAY
# -------------------------------------------------
@router.get("/execution/{execution_id}/replay")
async def replay_execution(execution_id: str):

    replay = replay_engine.replay_step_by_step(execution_id)

    if not replay:
        raise HTTPException(
            status_code=404,
            detail="Execution not found or empty replay"
        )

    return {
        "execution_id": execution_id,
        "replay": replay
    }


# -------------------------------------------------
# TOOL USAGE INSPECTOR
# -------------------------------------------------
@router.get("/execution/{execution_id}/tools")
async def tool_usage(execution_id: str):

    return replay_engine.get_tool_usage(execution_id)