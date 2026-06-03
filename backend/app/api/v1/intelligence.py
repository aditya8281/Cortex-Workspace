from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user_optional, get_db
from backend.app.intelligence.exclusions import ExclusionConfig
from backend.app.intelligence.memory_service import PersistentMemoryService
from backend.app.intelligence.models import RepositoryProfile
from backend.app.intelligence.permissions import PermissionService
from backend.app.intelligence.proactive_service import ProactiveService
from backend.app.intelligence.schemas import (
    AutomationSettingsResponse,
    AutomationSettingsUpdate,
    ExclusionConfigResponse,
    KnowledgeSearchResponse,
    ProactiveNotificationResponse,
    SystemActionPlanRequest,
)
from backend.app.intelligence.system_actions import SystemActionsService
from backend.app.models.user import User

router = APIRouter()
memory_service = PersistentMemoryService()
permission_service = PermissionService()
proactive_service = ProactiveService()
actions_service = SystemActionsService()


@router.get("/settings/automation", response_model=AutomationSettingsResponse)
def get_automation_settings(
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    settings = permission_service.get_settings(db, current_user.id if current_user else None)
    return AutomationSettingsResponse(
        automation_level=settings.automation_level,
        trusted_categories=sorted(permission_service.trusted_categories(settings)),
        observer_enabled=settings.observer_enabled,
    )


@router.put("/settings/automation", response_model=AutomationSettingsResponse)
def update_automation_settings(
    payload: AutomationSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    if payload.automation_level and payload.automation_level not in {
        "observation",
        "approval",
        "trusted",
    }:
        raise HTTPException(status_code=400, detail="Invalid automation_level")
    settings = permission_service.update_settings(
        db,
        user_id=current_user.id if current_user else None,
        automation_level=payload.automation_level,
        trusted_categories=payload.trusted_categories,
        observer_enabled=payload.observer_enabled,
    )
    db.commit()
    return AutomationSettingsResponse(
        automation_level=settings.automation_level,
        trusted_categories=sorted(permission_service.trusted_categories(settings)),
        observer_enabled=settings.observer_enabled,
    )


@router.get("/exclusions", response_model=ExclusionConfigResponse)
def get_exclusions():
    cfg = ExclusionConfig.load()
    return ExclusionConfigResponse(
        ignored_dir_names=sorted(cfg.ignored_dir_names),
        ignored_path_prefixes=list(cfg.ignored_path_prefixes),
        index_extensions=sorted(cfg.index_extensions),
        max_file_bytes=cfg.max_file_bytes,
    )


@router.get("/memory/search", response_model=KnowledgeSearchResponse)
def search_knowledge(
    q: str,
    limit: int = 8,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    results = memory_service.search(
        db, q, limit=limit, user_id=current_user.id if current_user else None
    )
    return KnowledgeSearchResponse(results=results)


@router.get("/repositories")
def list_repository_profiles(
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    import json

    q = db.query(RepositoryProfile)
    if current_user:
        q = q.filter(
            (RepositoryProfile.user_id == current_user.id)
            | (RepositoryProfile.user_id.is_(None))
        )
    rows = q.order_by(RepositoryProfile.updated_at.desc()).limit(50).all()
    return [
        {
            "path": row.path,
            "name": row.name,
            "summary": row.summary,
            "architecture_summary": row.architecture_summary,
            "tech_stack": row.tech_stack,
            "dependencies": json.loads(row.dependencies_json or "[]"),
            "entry_points": json.loads(row.entry_points_json or "[]"),
            "important_files": json.loads(row.important_files_json or "[]"),
            "updated_at": row.updated_at.isoformat(),
        }
        for row in rows
    ]


@router.get("/proactive", response_model=list[ProactiveNotificationResponse])
def list_proactive_notifications(
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    return proactive_service.list_active(
        db, user_id=current_user.id if current_user else None
    )


@router.post("/proactive/{notification_id}/dismiss")
def dismiss_proactive(notification_id: int, db: Session = Depends(get_db)):
    if not proactive_service.dismiss(db, notification_id):
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "dismissed"}


@router.post("/actions/plan")
def plan_system_action(
    payload: SystemActionPlanRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    return actions_service.plan_action(
        db,
        user_id=current_user.id if current_user else None,
        action_type=payload.action_type,
        description=payload.description,
        affected_paths=payload.affected_paths,
        payload=payload.payload,
        category=payload.category,
    )


@router.get("/actions/pending")
def list_pending_actions(
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    return actions_service.list_pending(
        db, user_id=current_user.id if current_user else None
    )


@router.post("/actions/{action_id}/approve")
def approve_action(action_id: int, db: Session = Depends(get_db)):
    return actions_service.approve_and_execute(db, action_id)


@router.post("/actions/{action_id}/reject")
def reject_action(action_id: int, db: Session = Depends(get_db)):
    return actions_service.reject(db, action_id)
