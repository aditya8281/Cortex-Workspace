from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user_optional, get_db
from backend.app.intelligence.schemas import SyncRunResponse, SyncStatusResponse
from backend.app.intelligence.sync_service import SyncService
from backend.app.models.user import User

router = APIRouter()
sync_service = SyncService()


def _run_sync_task(
    run_id: int,
    user_id: int | None,
    embedding_model: str | None,
    vector_db: str | None,
    code_parsing: str | None,
) -> None:
    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    try:
        sync_service.run_full_sync(
            db,
            user_id=user_id,
            run_id=run_id,
            embedding_model=embedding_model,
            vector_db=vector_db,
            code_parsing=code_parsing,
        )
    finally:
        db.close()


@router.get("/status", response_model=SyncStatusResponse)
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
    from fastapi import HTTPException

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
    if status.get("active_sync_id"):
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
    )
    db.refresh(run)
    return run
