from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from backend.app.services.health_service import HealthService

router = APIRouter()


@router.get("/health/live", status_code=status.HTTP_200_OK, response_model=dict)
async def liveness():
    return {"status": "alive"}


@router.get("/health/ready", status_code=status.HTTP_200_OK, response_model=dict)
async def readiness():
    database_ok = HealthService.check_database()
    status_text = "ready" if database_ok else "not_ready"
    return JSONResponse(
        status_code=200 if database_ok else 503,
        content={"status": status_text, "database": database_ok},
    )


@router.get("/health/deep", status_code=status.HTTP_200_OK, response_model=dict)
async def deep_health():
    result = HealthService.check_all()
    status_code = 200 if result["status"] == "healthy" else 503
    return JSONResponse(status_code=status_code, content=result)
