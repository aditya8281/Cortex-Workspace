from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user_optional, get_db
from backend.app.intelligence.models import SyncRun
from backend.app.intelligence.schemas import SyncRunResponse
from backend.app.intelligence.sync_service import SyncService
from backend.app.models.user import User
from backend.app.services.workspace_intelligence_service import WorkspaceIntelligenceService

router = APIRouter()
service = WorkspaceIntelligenceService()
sync_service = SyncService()


def _run_workspace_sync_task(run_id: int, user_id: int | None) -> None:
    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                sync_service.run_full_sync(
                    db,
                    user_id=user_id,
                    run_id=run_id,
                    force=False,
                )
            )
        finally:
            loop.close()
    finally:
        db.close()


@router.get("/intelligence")
def get_workspace_intelligence():
    return service.build_report()


@router.post("/sync", response_model=SyncRunResponse)
def trigger_workspace_sync(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    user_id = current_user.id if current_user else None
    run = SyncRun(
        user_id=user_id,
        status="running",
        progress_message="Queued workspace sync...",
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    sync_service._active_run_id = run.id

    background_tasks.add_task(
        _run_workspace_sync_task,
        run.id,
        user_id,
    )
    return run
