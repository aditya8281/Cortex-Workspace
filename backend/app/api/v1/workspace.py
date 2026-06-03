from fastapi import APIRouter

from backend.app.services.workspace_intelligence_service import WorkspaceIntelligenceService

router = APIRouter()
service = WorkspaceIntelligenceService()


@router.get("/intelligence")
def get_workspace_intelligence():
    return service.build_report()
