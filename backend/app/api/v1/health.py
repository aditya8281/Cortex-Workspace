from fastapi import APIRouter, status

from backend.app.services.health_service import HealthService

router = APIRouter()


@router.get(
    "/health/live",
    status_code=status.HTTP_200_OK
)
async def liveness():
    return {"status": "alive"}


@router.get(
    "/health/ready",
    status_code=status.HTTP_200_OK
)
async def readiness():
    database_ok = HealthService.check_database()

    if not database_ok:
        return {
            "status": "not_ready",
            "database": False,
        }

    return {
        "status": "ready",
        "database": True,
    }


@router.get(
    "/health/deep",
    status_code=status.HTTP_200_OK
)
async def deep_health():
    database_ok = HealthService.check_database()

    return {
        "status": "healthy" if database_ok else "degraded",
        "checks": {
            "database": database_ok,
        },
    }
