from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user_optional, get_db
from backend.app.intelligence.schemas import SyncRunResponse
from backend.app.intelligence.sync_service import SyncService
from backend.app.models.user import User

router = APIRouter()
sync_service = SyncService()


class PathRequest(BaseModel):
    path: str


def _run_sync_task(
    run_id: int,
    user_id: int | None,
    embedding_model: str | None,
    vector_db: str | None,
    code_parsing: str | None,
    force: bool = False,
) -> None:
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
                    embedding_model=embedding_model,
                    vector_db=vector_db,
                    code_parsing=code_parsing,
                    force=force,
                )
            )
        finally:
            loop.close()
    finally:
        db.close()


@router.get("/status")
def get_sync_status(db: Session = Depends(get_db)):
    return sync_service.get_status(db)


@router.get("/runs/latest", response_model=SyncRunResponse | None)
def get_latest_sync_run(db: Session = Depends(get_db)):
    from backend.app.intelligence.models import SyncRun

    run = db.query(SyncRun).order_by(SyncRun.started_at.desc()).first()
    return run


@router.get("/runs/{run_id}", response_model=SyncRunResponse)
def get_sync_run(run_id: int, db: Session = Depends(get_db)):
    from backend.app.intelligence.models import SyncRun

    run = db.get(SyncRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Sync run not found")
    return run


@router.post("/now", response_model=SyncRunResponse)
def sync_now(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
    embedding_model: str | None = None,
    vector_db: str | None = None,
    code_parsing: str | None = None,
):
    user_id = current_user.id if current_user else None
    status = sync_service.get_status(db)
    if status.get("active_sync_status") == "syncing":
        from backend.app.intelligence.models import SyncRun

        active = db.get(SyncRun, status["active_sync_id"])
        if active and active.status == "running":
            return active

    from backend.app.intelligence.models import SyncRun

    run = SyncRun(
        user_id=user_id,
        status="running",
        progress_message="Queued full environment sync...",
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    sync_service._active_run_id = run.id

    background_tasks.add_task(
        _run_sync_task,
        run.id,
        user_id,
        embedding_model,
        vector_db,
        code_parsing,
        False
    )
    db.refresh(run)
    return run


@router.post("/pause")
def pause_sync():
    sync_service.pause_sync()
    return {"status": "success", "message": "Sync paused"}


@router.post("/resume")
def resume_sync():
    sync_service.resume_sync()
    return {"status": "success", "message": "Sync resumed"}


@router.post("/cancel")
def cancel_sync(db: Session = Depends(get_db)):
    sync_service.cancel_sync()
    
    # Mark running runs in DB as failed/cancelled
    from backend.app.intelligence.models import SyncRun
    running_runs = db.query(SyncRun).filter(SyncRun.status == "running").all()
    for run in running_runs:
        run.status = "failed"
        run.progress_message = "Sync cancelled by user"
    db.commit()
    return {"status": "success", "message": "Sync cancelled"}


@router.post("/force", response_model=SyncRunResponse)
def force_resync(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
    embedding_model: str | None = None,
    vector_db: str | None = None,
    code_parsing: str | None = None,
):
    # Triggers full indexing from a clean slate
    user_id = current_user.id if current_user else None
    sync_service.cancel_sync()
    
    from backend.app.intelligence.models import SyncRun
    run = SyncRun(
        user_id=user_id,
        status="running",
        progress_message="Queued forced environment sync...",
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    sync_service._active_run_id = run.id

    background_tasks.add_task(
        _run_sync_task,
        run.id,
        user_id,
        embedding_model,
        vector_db,
        code_parsing,
        True
    )
    db.refresh(run)
    return run


@router.get("/config")
def get_scope_config():
    from backend.app.intelligence.scope_config import SyncScopeConfig
    config = SyncScopeConfig()
    return {
        "include_folders": config.include_folders,
        "exclude_folders": config.exclude_folders,
        "priority_folders": config.priority_folders,
        "ignore_patterns": config.ignore_patterns,
        "auto_sync_enabled": config.auto_sync_enabled
    }


@router.post("/config/include")
def add_include_folder(payload: PathRequest):
    from backend.app.intelligence.scope_config import SyncScopeConfig
    config = SyncScopeConfig()
    path_str = payload.path.strip()
    if not path_str:
         raise HTTPException(status_code=400, detail="Path cannot be empty")
    if path_str not in config.include_folders:
        config.include_folders.append(path_str)
        config.save()
    return {"status": "success", "include_folders": config.include_folders}


@router.post("/config/exclude")
def add_exclude_folder(payload: PathRequest):
    from backend.app.intelligence.scope_config import SyncScopeConfig
    config = SyncScopeConfig()
    path_str = payload.path.strip()
    if not path_str:
         raise HTTPException(status_code=400, detail="Path cannot be empty")
    if path_str not in config.exclude_folders:
        config.exclude_folders.append(path_str)
        config.save()
    return {"status": "success", "exclude_folders": config.exclude_folders}


@router.post("/config/include/remove")
def remove_include_folder(payload: PathRequest):
    from backend.app.intelligence.scope_config import SyncScopeConfig
    config = SyncScopeConfig()
    path_str = payload.path.strip()
    if path_str in config.include_folders:
        config.include_folders.remove(path_str)
        config.save()
    return {"status": "success", "include_folders": config.include_folders}


@router.post("/config/exclude/remove")
def remove_exclude_folder(payload: PathRequest):
    from backend.app.intelligence.scope_config import SyncScopeConfig
    config = SyncScopeConfig()
    path_str = payload.path.strip()
    if path_str in config.exclude_folders:
        config.exclude_folders.remove(path_str)
        config.save()
    return {"status": "success", "exclude_folders": config.exclude_folders}
