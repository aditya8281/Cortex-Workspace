from fastapi import APIRouter
from fastapi import status

from backend.app.services.health_service import HealthService

router = APIRouter()


@router.get(
    "/health/live",
    status_code=status.HTTP_200_OK
)
async def liveness():

    return {
        "status": "alive"
    }


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

    memory_ok = HealthService.check_memory()

    overall = all(
        [
            database_ok,
            memory_ok,
        ]
    )

    return {
        "status": (
            "healthy"
            if overall
            else "degraded"
        ),
        "checks": {
            "database": database_ok,
            "memory": memory_ok,
        },
    }

from fastapi import HTTPException
from backend.app.services.memory_manager import memory_manager

@router.get(
    "/health/services",
    status_code=status.HTTP_200_OK
)
async def list_services():
    services_list = []
    
    # 1. API Gateway
    services_list.append({
        "name": "API Gateway",
        "status": "running",
        "uptime": "active"
    })
    
    # 2. Memory Vault
    memory_ok = HealthService.check_memory()
    services_list.append({
        "name": "Memory Vault",
        "status": "running" if memory_ok else "error",
        "uptime": "active" if memory_ok else "degraded"
    })
    
    # 4. Sync Engine (File Watcher)
    watcher = memory_manager._services.get("file_watcher")
    watcher_running = watcher is not None and getattr(watcher, "_thread", None) is not None
    services_list.append({
        "name": "Sync Engine",
        "status": "running" if watcher_running else "idle",
        "uptime": "active" if watcher_running else "stopped"
    })
    
    # 5. Observer Service (Observer)
    observer = memory_manager._services.get("observer")
    observer_running = observer is not None and getattr(observer, "_thread", None) is not None
    services_list.append({
        "name": "Observer Service",
        "status": "running" if observer_running else "idle",
        "uptime": "active" if observer_running else "stopped"
    })
    
    return services_list

@router.post(
    "/health/services/{name}/restart",
    status_code=status.HTTP_200_OK
)
async def restart_service(name: str):
    if name == "Sync Engine":
        watcher = memory_manager._services.get("file_watcher")
        if watcher:
            watcher.stop()
            watcher.start()
            return {"message": "Sync Engine restarted successfully"}
        raise HTTPException(status_code=404, detail="Sync Engine service not found")
        
    elif name == "Observer Service":
        observer = memory_manager._services.get("observer")
        if observer:
            observer.stop()
            observer.start()
            return {"message": "Observer Service restarted successfully"}
        raise HTTPException(status_code=404, detail="Observer Service service not found")
        
    elif name == "Memory Vault":
        from backend.app.db.session import reset_db_engine
        reset_db_engine()
        return {"message": f"{name} database engine reset/restarted successfully"}
        
    elif name == "API Gateway":
        return {"message": "API Gateway is active and cannot be restarted remotely"}
        
    raise HTTPException(status_code=404, detail=f"Service '{name}' not found")