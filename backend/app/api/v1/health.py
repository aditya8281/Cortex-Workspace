from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from backend.app.services.health_service import HealthService

router = APIRouter()


@router.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness():
    return {"status": "alive"}


@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness():
    database_ok = HealthService.check_database()
    status_text = "ready" if database_ok else "not_ready"
    return JSONResponse(
        status_code=200 if database_ok else 503,
        content={"status": status_text, "database": database_ok},
    )


@router.get("/health/deep", status_code=status.HTTP_200_OK)
async def deep_health():
    database_ok = HealthService.check_database()
    redis_ok = HealthService.check_redis()
    ollama_ok = HealthService.check_ollama()

    all_ok = database_ok and redis_ok and ollama_ok
    return {
        "status": "healthy" if all_ok else "degraded",
        "checks": {
            "database": database_ok,
            "redis": redis_ok,
            "ollama": ollama_ok,
        },
    }
