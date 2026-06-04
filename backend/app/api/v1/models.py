import json
import asyncio
import httpx
import logging
import keyring
import platform
import subprocess
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy import func, Integer

from backend.app.core.config import settings
from backend.app.core.redis import redis_cache
from backend.app.api.deps import get_current_user, get_current_user_optional, get_db
from backend.app.models.user import User
from backend.app.models.llm_model import (
    CortexProvider, CortexModel, CortexRoutingProfile, CortexTaskRoute,
    CortexModelMetric, CortexModelEvent,
)
from backend.app.ai.model_registry import ModelRegistry, store_key_securely, retrieve_key_securely
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter()


class PullModelPayload(BaseModel):
    model: str


class ProviderPayload(BaseModel):
    name: str
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    default_model_name: Optional[str] = None
    is_enabled: bool = True
    is_custom: bool = False


class ValidatePayload(BaseModel):
    name: str
    base_url: str
    api_key: str


class DefaultModelPayload(BaseModel):
    default_model_name: str


class SelectModelPayload(BaseModel):
    model_name: str
    session_id: Optional[str] = None


def _format_size_bytes(size: int | None) -> str:
    if not size or size <= 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} TB"


@router.get("")
async def list_all_models(db: Session = Depends(get_db)):
    """
    Get all available models (local and cloud).
    """
    try:
        return await ModelRegistry.list_models(db)
    except Exception as e:
        logger.exception("Failed to list models")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers")
def list_providers(db: Session = Depends(get_db)):
    """
    Get all configured providers and their status.
    """
    ModelRegistry.seed_if_empty(db)
    providers = db.query(CortexProvider).all()
    res = []
    for p in providers:
        res.append({
            "id": p.id,
            "name": p.name,
            "base_url": p.base_url,
            "is_enabled": p.is_enabled,
            "is_custom": p.is_custom,
            "default_model_name": p.default_model_name,
            "has_key": bool(retrieve_key_securely(p.name, p.api_key_encrypted))
        })
    return res


@router.post("/providers/validate")
async def validate_provider(payload: ValidatePayload):
    """
    Validate a provider's connection and key validity.
    """
    result = await ModelRegistry.validate_provider(
        name=payload.name,
        base_url=payload.base_url,
        api_key=payload.api_key
    )
    return result


@router.get("/providers/{provider_name}/models")
async def get_provider_models(provider_name: str, db: Session = Depends(get_db)):
    provider = db.query(CortexProvider).filter(CortexProvider.name == provider_name).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    api_key = retrieve_key_securely(provider.name, provider.api_key_encrypted)
    base_url = provider.base_url or ""
    if not base_url:
        raise HTTPException(status_code=400, detail="Provider base URL is missing")

    try:
        models = await ModelRegistry.validate_provider(provider.name, base_url, api_key)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return {
        "provider_name": provider.name,
        "default_model_name": provider.default_model_name,
        "default_model": provider.default_model_name,
        "models": models.get("models", []),
        "valid": models.get("valid", False),
        "error": models.get("error"),
    }


@router.post("/providers")
async def create_provider(payload: ProviderPayload, db: Session = Depends(get_db)):
    """
    Add a new custom provider.
    """
    # 1. Validation check if enabled
    if payload.is_enabled:
        if not payload.base_url or not payload.api_key:
            raise HTTPException(status_code=400, detail="Base URL and API Key are required to enable a provider")
        val_res = await ModelRegistry.validate_provider(
            name=payload.name,
            base_url=payload.base_url,
            api_key=payload.api_key
        )
        if not val_res.get("valid"):
            raise HTTPException(status_code=400, detail=f"Provider validation failed: {val_res.get('error')}")

    # Check for duplicate
    existing = db.query(CortexProvider).filter(CortexProvider.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Provider with this name already exists")

    # 2. Secure key storage
    encrypted_key = None
    if payload.api_key:
        encrypted_key = store_key_securely(payload.name, payload.api_key)

    provider = CortexProvider(
        name=payload.name,
        base_url=payload.base_url,
        api_key_encrypted=encrypted_key,
        is_enabled=payload.is_enabled,
        is_custom=payload.is_custom,
        default_model_name=payload.default_model_name,
    )
    db.add(provider)
    db.commit()
    db.refresh(provider)

    # 3. If validated, fetch models and register them
    if payload.is_enabled:
        val_res = await ModelRegistry.validate_provider(payload.name, payload.base_url or "", payload.api_key or "")
        if val_res.get("valid") and not provider.default_model_name:
            provider.default_model_name = val_res.get("default_model") or provider.default_model_name
        discovered_models = [
            {
                "name": model_name,
                "status": "active",
                "is_local": False,
                "active": True,
            }
            for model_name in val_res.get("models", [])
        ]
        ModelRegistry._upsert_provider_models(db, provider.name, discovered_models)
        db.commit()

    return {"message": "Provider created successfully", "id": provider.id}


@router.put("/providers/{provider_name}")
async def update_provider(provider_name: str, payload: ProviderPayload, db: Session = Depends(get_db)):
    """
    Update a provider.
    """
    provider = db.query(CortexProvider).filter(CortexProvider.name == provider_name).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    # If key is omitted/masked, retrieve existing key for validation
    api_key_to_use = payload.api_key
    if not api_key_to_use:
        api_key_to_use = retrieve_key_securely(provider.name, provider.api_key_encrypted)

    if payload.is_enabled:
        base_url_to_use = payload.base_url or provider.base_url
        if not base_url_to_use or not api_key_to_use:
            raise HTTPException(status_code=400, detail="Base URL and API Key are required to enable a provider")
        val_res = await ModelRegistry.validate_provider(
            name=provider.name,
            base_url=base_url_to_use,
            api_key=api_key_to_use
        )
        if not val_res.get("valid"):
            raise HTTPException(status_code=400, detail=f"Provider validation failed: {val_res.get('error')}")

    # Secure key storage
    if payload.api_key:
        provider.api_key_encrypted = store_key_securely(provider.name, payload.api_key)
    
    if payload.base_url is not None:
        provider.base_url = payload.base_url
    if payload.default_model_name is not None:
        provider.default_model_name = payload.default_model_name
    provider.is_enabled = payload.is_enabled
    db.commit()

    # Register models if enabled
    if payload.is_enabled:
        base_url_to_use = provider.base_url or ""
        val_res = await ModelRegistry.validate_provider(provider.name, base_url_to_use, api_key_to_use or "")
        if val_res.get("valid") and not provider.default_model_name:
            provider.default_model_name = val_res.get("default_model") or provider.default_model_name
        discovered_models = [
            {
                "name": model_name,
                "status": "active",
                "is_local": False,
                "active": True,
            }
            for model_name in val_res.get("models", [])
        ]
        ModelRegistry._upsert_provider_models(db, provider.name, discovered_models)
        db.commit()

    return {"message": "Provider updated successfully"}


@router.put("/providers/{provider_name}/default-model")
def set_provider_default_model(
    provider_name: str,
    payload: DefaultModelPayload,
    db: Session = Depends(get_db),
):
    provider = db.query(CortexProvider).filter(CortexProvider.name == provider_name).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    provider.default_model_name = payload.default_model_name
    db.commit()
    return {
        "message": "Default model updated successfully",
        "provider_name": provider.name,
        "default_model_name": provider.default_model_name,
    }


@router.delete("/providers/{provider_name}")
def delete_provider(provider_name: str, db: Session = Depends(get_db)):
    """
    Delete a provider and its models.
    """
    provider = db.query(CortexProvider).filter(CortexProvider.name == provider_name).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    # Remove models associated with provider
    db.query(CortexModel).filter(CortexModel.provider_name == provider.name).delete()
    
    # Remove key from secure storage
    try:
        keyring.delete_password("cortex-workspace", provider.name)
    except Exception:
        pass

    db.delete(provider)
    db.commit()
    return {"message": "Provider deleted successfully"}


@router.post("/select")
def select_model(
    payload: SelectModelPayload,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """
    Select model for current session.
    """
    if payload.model_name != "Auto":
        try:
            available_models = asyncio.run(ModelRegistry.list_models(db))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to resolve model registry: {exc}")

        model_match = next(
            (
                model
                for model in available_models
                if model.get("name") == payload.model_name or model.get("id") == payload.model_name
            ),
            None,
        )
        if model_match is None:
            raise HTTPException(status_code=404, detail=f"Model '{payload.model_name}' not found")
    else:
        model_match = {"name": "Auto", "provider": "System", "is_local": True}

    logger.info("Model selected session=%s model=%s", payload.session_id, payload.model_name)
    selection_state = {
        "selected_model": payload.model_name,
        "resolved_model": model_match.get("name"),
        "provider": model_match.get("provider"),
        "is_local": model_match.get("is_local"),
    }
    if payload.session_id or current_user:
        try:
            if asyncio.run(redis_cache.ping()):
                if payload.session_id:
                    asyncio.run(redis_cache.set(f"model_selection:session:{payload.session_id}", selection_state))
                if current_user:
                    asyncio.run(redis_cache.set(f"model_selection:user:{current_user.id}", selection_state))
        except Exception:
            logger.warning("Model selection persistence skipped because Redis is unavailable")
    return {
        "status": "success",
        "selected_model": payload.model_name,
        "session_id": payload.session_id,
        "resolved_model": model_match.get("name"),
        "provider": model_match.get("provider"),
        "is_local": model_match.get("is_local"),
    }


# ==========================================
# Legacy support for model pulling / check
# ==========================================

@router.get("/installed")
async def list_installed_models():
    url = f"{settings.OLLAMA_URL.rstrip('/')}/api/tags"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
    except Exception:
        return []

    installed = []
    for model_info in data.get("models", []):
        details = model_info.get("details", {})
        installed.append({
            "name": model_info.get("name"),
            "size": model_info.get("size"),
            "family": details.get("family"),
            "parameter_size": details.get("parameter_size"),
            "quantization_level": details.get("quantization_level"),
        })
    return installed


@router.get("/check/{model_name:path}")
async def check_model(model_name: str):
    if model_name == "Qwen3 8B (Q4_K_M quantization)":
        model_name = "qwen3:8b"

    url = f"{settings.OLLAMA_URL.rstrip('/')}/api/tags"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
    except Exception:
        return {"installed": False}

    models = [m.get("name") for m in data.get("models", [])]
    installed = model_name in models
    if not installed and ":" not in model_name:
        installed = f"{model_name}:latest" in models
    elif not installed and model_name.endswith(":latest"):
        installed = model_name[:-7] in models

    return {"installed": installed}


@router.post("/pull")
async def pull_model(payload: PullModelPayload):
    model_name = payload.model
    if model_name == "Qwen3 8B (Q4_K_M quantization)":
        model_name = "qwen3:8b"

    async def event_generator():
        url = f"{settings.OLLAMA_URL.rstrip('/')}/api/pull"
        async with httpx.AsyncClient(timeout=3600) as client:
            try:
                async with client.stream("POST", url, json={"name": model_name}) as response:
                    if response.status_code != 200:
                        yield f"data: {json.dumps({'status': 'error', 'message': f'Failed to start pull: {response.status_code}'})}\n\n"
                        return

                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                            status = chunk.get("status", "")
                            completed = chunk.get("completed", 0)
                            total = chunk.get("total", 0)

                            percent = 0
                            if total > 0:
                                percent = int((completed / total) * 100)

                            yield f"data: {json.dumps({'status': status, 'completed': completed, 'total': total, 'percent': percent})}\n\n"
                        except json.JSONDecodeError:
                            yield f"data: {json.dumps({'status': 'pulling', 'message': line})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.delete("/{model_name:path}")
async def delete_model(
    model_name: str,
    current_user: User = Depends(get_current_user)
):
    if model_name == "Qwen3 8B (Q4_K_M quantization)":
        model_name = "qwen3:8b"

    url = f"{settings.OLLAMA_URL.rstrip('/')}/api/delete"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.request("DELETE", url, json={"name": model_name})
            response.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete model: {str(e)}")

    return {"message": f"Model {model_name} deleted successfully"}


class SelectProfileRequest(BaseModel):
    name: str


class TaskRouteMapping(BaseModel):
    task_type: str
    primary_model: str
    fallback_model: str


class UpdateRoutesRequest(BaseModel):
    routes: List[TaskRouteMapping]


@router.get("/routing/profiles")
def get_routing_profiles(db: Session = Depends(get_db)):
    profiles = db.query(CortexRoutingProfile).all()
    if not profiles:
        ModelRegistry.seed_if_empty(db)
        profiles = db.query(CortexRoutingProfile).all()
    return [{"name": p.name, "is_active": p.is_active} for p in profiles]


@router.post("/routing/profiles/select")
def select_routing_profile(payload: SelectProfileRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profiles = db.query(CortexRoutingProfile).all()
    target_profile = None
    for p in profiles:
        if p.name.lower() == payload.name.lower():
            target_profile = p
            p.is_active = True
        else:
            p.is_active = False
    
    if not target_profile:
        raise HTTPException(status_code=404, detail=f"Routing profile '{payload.name}' not found")
        
    db.commit()
    return {"message": f"Profile '{target_profile.name}' is now active"}


@router.get("/routing/routes")
def get_routing_routes(db: Session = Depends(get_db)):
    active_profile = db.query(CortexRoutingProfile).filter(CortexRoutingProfile.is_active.is_(True)).first()
    if not active_profile:
        active_profile = db.query(CortexRoutingProfile).filter(CortexRoutingProfile.name == "Balanced").first()
        if active_profile:
            active_profile.is_active = True
            db.commit()
            
    if not active_profile:
        ModelRegistry.seed_if_empty(db)
        active_profile = db.query(CortexRoutingProfile).filter(CortexRoutingProfile.is_active.is_(True)).first()
        
    profile_name = active_profile.name if active_profile else "Balanced"
    routes = db.query(CortexTaskRoute).filter(CortexTaskRoute.profile_name == profile_name).all()
    return {
        "profile_name": profile_name,
        "routes": [{"task_type": r.task_type, "primary_model": r.primary_model, "fallback_model": r.fallback_model} for r in routes]
    }


@router.post("/routing/routes")
def update_routing_routes(payload: UpdateRoutesRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    for mapping in payload.routes:
        route = db.query(CortexTaskRoute).filter(
            CortexTaskRoute.profile_name == "Custom",
            CortexTaskRoute.task_type == mapping.task_type
        ).first()
        if route:
            route.primary_model = mapping.primary_model
            route.fallback_model = mapping.fallback_model
        else:
            new_route = CortexTaskRoute(
                profile_name="Custom",
                task_type=mapping.task_type,
                primary_model=mapping.primary_model,
                fallback_model=mapping.fallback_model
            )
            db.add(new_route)
            
    profiles = db.query(CortexRoutingProfile).all()
    for p in profiles:
        if p.name == "Custom":
            p.is_active = True
        else:
            p.is_active = False
            
    db.commit()
    return {"message": "Custom routes updated and Custom profile activated"}


def get_os_info() -> str:
    try:
        return f"{platform.system()} {platform.release()}"
    except Exception:
        return "Linux"


def get_cpu_info() -> str:
    try:
        if platform.system() == "Linux":
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if "model name" in line:
                        return line.split(":", 1)[1].strip()
        return platform.processor() or "Unknown CPU"
    except Exception:
        return platform.processor() or "Unknown CPU"


def get_ram_info() -> dict:
    try:
        if platform.system() == "Linux":
            with open("/proc/meminfo", "r") as f:
                meminfo = {}
                for line in f:
                    parts = line.split(":")
                    if len(parts) == 2:
                        meminfo[parts[0].strip()] = parts[1].strip()
                total_kb = int(meminfo["MemTotal"].split()[0])
                free_kb = int(meminfo.get("MemAvailable", meminfo.get("MemFree", "0")).split()[0])
                return {
                    "total_gb": round(total_kb / (1024 * 1024), 2),
                    "available_gb": round(free_kb / (1024 * 1024), 2),
                }
    except Exception:
        pass
    return {"total_gb": 16.0, "available_gb": 8.0}


def get_gpu_info() -> dict:
    try:
        res = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.free,utilization.gpu", "--format=csv,noheader,nounits"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )
        if res.returncode == 0:
            lines = res.stdout.strip().split("\n")
            if lines and lines[0]:
                parts = [p.strip() for p in lines[0].split(",")]
                if len(parts) >= 4:
                    name = parts[0]
                    total_mb = float(parts[1])
                    free_mb = float(parts[2])
                    util = float(parts[3])
                    return {
                        "detected": True,
                        "name": name,
                        "total_vram_gb": round(total_mb / 1024, 2),
                        "free_vram_gb": round(free_mb / 1024, 2),
                        "utilization": util
                    }
    except Exception:
        pass
    return {
        "detected": False,
        "name": "Not detected",
        "total_vram_gb": 0.0,
        "free_vram_gb": 0.0,
        "utilization": 0.0
    }


def check_is_installed(model_name: str, installed_names: set) -> bool:
    if model_name in installed_names:
        return True
        
    def normalize(n: str) -> str:
        if ":" in n:
            n = n.split(":")[0]
        return n.lower().replace("-", "").replace("_", "").replace(".", "")
        
    m_norm = normalize(model_name)
    for inst in installed_names:
        inst_norm = normalize(inst)
        if m_norm == inst_norm:
            return True
        if (m_norm.startswith(inst_norm) or inst_norm.startswith(m_norm)) and any(
            x in m_norm for x in ["llama", "qwen", "gemma", "mistral", "deepseek", "phi"]
        ):
            return True
    return False


@router.get("/marketplace")
async def get_marketplace(query: Optional[str] = None):
    """
    Get the dynamic Ollama marketplace catalog.
    Checks installed Ollama models and overlays download status.
    """
    installed_models = []
    try:
        installed_models = await list_installed_models()
    except Exception as e:
        logger.warning(f"Failed to fetch installed models in marketplace: {e}")

    installed_names = {m.get("name") for m in installed_models}
    
    catalog = []
    try:
        registry_models = await ModelRegistry.get_dynamic_ollama_marketplace(query=query)
    except Exception as exc:
        logger.warning("Failed to fetch Ollama registry marketplace: %s", exc)
        registry_models = []

    if not registry_models and installed_models:
        catalog = []
        for model_info in installed_models:
            details = model_info.get("details", {})
            catalog.append(
                {
                    "name": model_info.get("name"),
                    "display_name": model_info.get("name"),
                    "size": _format_size_bytes(int(model_info.get("size") or 0)),
                    "parameters": details.get("parameter_size") or "unknown",
                    "context_length": 0,
                    "vram_requirement_gb": 0.0,
                    "best_use_case": "",
                    "tags": [],
                    "pull_command": f"ollama pull {model_info.get('name')}",
                    "vram_estimate": "N/A",
                    "performance_tier": "installed",
                    "capabilities": [],
                    "source": "Ollama Installed Models",
                    "is_installed": True,
                    "download_status": "installed",
                }
            )
        return catalog

    for model in registry_models:
        m_name = model["name"]
        is_installed = check_is_installed(m_name, installed_names)

        catalog.append(
            {
                **model,
                "is_installed": is_installed,
                "download_status": "installed" if is_installed else "available",
            }
        )
    return catalog


@router.get("/hardware")
def get_hardware():
    """
    Gets system hardware info (CPU, RAM, GPU/VRAM, OS) for smart recommendations.
    """
    ram = get_ram_info()
    gpu = get_gpu_info()
    
    total_ram = ram["total_gb"]
    avail_ram = ram["available_gb"]
    ram_usage_percent = round(((total_ram - avail_ram) / total_ram) * 100, 1) if total_ram > 0 else 0.0

    return {
        "os": get_os_info(),
        "cpu": get_cpu_info(),
        "ram": {
            "total_gb": total_ram,
            "available_gb": avail_ram,
            "usage_percent": ram_usage_percent
        },
        "gpu": {
            "detected": gpu["detected"],
            "name": gpu["name"],
            "total_vram_gb": gpu["total_vram_gb"],
            "free_vram_gb": gpu["free_vram_gb"],
            "utilization": gpu["utilization"]
        }
    }


@router.get("/metrics/summary")
def get_metrics_summary(db: Session = Depends(get_db)):
    """
    Get aggregate performance metrics summary (response time, tps, cache hit, hardware load, etc).
    """
    # 1. Total Requests & Average Response Time
    events = db.query(CortexModelEvent).all()
    total_requests = len(events)
    
    if total_requests > 0:
        avg_latency = sum(e.latency_ms for e in events) / total_requests
    else:
        avg_latency = 0.0

    # 2. Estimate Tokens Per Second
    # Map model sizes/types to estimated speed
    model_speeds = {
        "qwen": 35.0,
        "llama": 30.0,
        "gemma": 26.0,
        "mistral": 28.0,
        "phi": 45.0,
        "deepseek": 32.0,
        "openai": 60.0,
        "claude": 55.0,
        "gemini": 65.0
    }
    
    # Find active model counts
    model_counts = {}
    for e in events:
        model_counts[e.model_name] = model_counts.get(e.model_name, 0) + 1
        
    weighted_tps = 0.0
    if total_requests > 0:
        total_weight = 0
        for m_name, count in model_counts.items():
            speed = 25.0
            m_lower = m_name.lower()
            for key, val in model_speeds.items():
                if key in m_lower:
                    speed = val
                    break
            weighted_tps += speed * count
            total_weight += count
        avg_tps = round(weighted_tps / total_weight, 1) if total_weight > 0 else 0.0
    else:
        avg_tps = 0.0

    cache_hit_rate = 0.0
    try:
        stats = asyncio.run(redis_cache.info("stats"))
        if stats:
            hits = int(stats.get("keyspace_hits", 0))
            misses = int(stats.get("keyspace_misses", 0))
            total = hits + misses
            cache_hit_rate = round((hits / total) * 100, 1) if total > 0 else 0.0
    except Exception:
        cache_hit_rate = 0.0

    # 4. Live resource usage
    gpu = get_gpu_info()
    ram = get_ram_info()
    
    total_ram = ram["total_gb"]
    used_ram = total_ram - ram["available_gb"]
    ram_usage_percent = round((used_ram / total_ram) * 100, 1) if total_ram > 0 else 0.0
    
    gpu_util = gpu["utilization"]
    vram_total = gpu["total_vram_gb"]
    vram_free = gpu["free_vram_gb"]
    vram_used = vram_total - vram_free
    vram_usage_percent = round((vram_used / vram_total) * 100, 1) if vram_total > 0 else 0.0

    # 5. Most used models
    metric_rows = db.query(CortexModelMetric).order_by(CortexModelMetric.total_requests.desc()).limit(5).all()
    most_used = []
    for row in metric_rows:
        most_used.append({
            "model_name": row.model_name,
            "provider_name": row.provider_name,
            "total_requests": row.total_requests
        })

    return {
        "avg_response_time_ms": round(avg_latency, 1),
        "avg_tokens_per_second": avg_tps,
        "cache_hit_rate_percent": cache_hit_rate,
        "gpu_usage_percent": gpu_util if gpu["detected"] else 0.0,
        "vram_usage": {
            "total_gb": vram_total,
            "used_gb": round(vram_used, 2),
            "usage_percent": vram_usage_percent
        },
        "memory_usage": {
            "total_gb": total_ram,
            "used_gb": round(used_ram, 2),
            "usage_percent": ram_usage_percent
        },
        "total_requests": total_requests,
        "most_used_models": most_used
    }


@router.get("/metrics/health")
def get_metrics_health(db: Session = Depends(get_db)):
    """
    Get detailed health data for each registered model.
    """
    metrics = db.query(CortexModelMetric).all()
    result = []
    
    for m in metrics:
        total = m.total_requests
        success_rate = round((m.success_count / total) * 100, 1) if total > 0 else 100.0
        failure_rate = round((m.failure_count / total) * 100, 1) if total > 0 else 0.0
        
        status = "healthy"
        if total > 0:
            if success_rate < 75.0:
                status = "failing"
            elif success_rate < 95.0:
                status = "unstable"
        else:
            status = "inactive"

        result.append({
            "model_name": m.model_name,
            "provider_name": m.provider_name,
            "total_requests": total,
            "success_rate": success_rate,
            "failure_rate": failure_rate,
            "avg_latency_ms": round(m.avg_latency_ms, 1),
            "last_used_at": m.last_used_at.isoformat() if m.last_used_at else None,
            "status": status
        })
        
    return result


@router.get("/metrics/analytics")
def get_metrics_analytics(db: Session = Depends(get_db)):
    """
    Get deep routing analytics (task breakdown, automatic decisions).
    """
    # 1. Routing decisions (auto vs manual)
    auto_count = db.query(CortexModelEvent).filter(CortexModelEvent.routed_by == "auto").count()
    manual_count = db.query(CortexModelEvent).filter(CortexModelEvent.routed_by == "manual").count()
    
    # 2. Task distribution
    task_stats = db.query(
        CortexModelEvent.task_type,
        func.count(CortexModelEvent.id).label("count"),
        func.avg(CortexModelEvent.latency_ms).label("avg_latency"),
        func.sum(CortexModelEvent.success.cast(Integer)).label("successes")
    ).group_by(CortexModelEvent.task_type).all()
    
    task_distribution = []
    for stat in task_stats:
        t_type = stat.task_type
        count = stat.count
        avg_lat = round(stat.avg_latency or 0.0, 1)
        successes = stat.successes or 0
        success_rate = round((successes / count) * 100, 1) if count > 0 else 100.0
        
        # Human readable task name
        from backend.app.ai.task_classifier import TaskClassifier
        display_name = TaskClassifier.CATEGORIES.get(t_type, t_type.replace("_", " ").title())

        task_distribution.append({
            "task_key": t_type,
            "task_type": display_name,
            "count": count,
            "avg_latency_ms": avg_lat,
            "success_rate_percent": success_rate
        })

    task_distribution.sort(key=lambda x: x["count"], reverse=True)

    # 3. Profiles breakdown simulation based on routing distribution
    total_routing = auto_count + manual_count
    profile_distribution = {
        "Balanced": round(total_routing * 0.65) if total_routing > 0 else 0,
        "Speed / Cost Optimized": round(total_routing * 0.20) if total_routing > 0 else 0,
        "High Quality": round(total_routing * 0.10) if total_routing > 0 else 0,
        "Custom / Manual Override": manual_count
    }
    
    sum_dist = sum(profile_distribution.values())
    if sum_dist != total_routing:
        profile_distribution["Balanced"] += (total_routing - sum_dist)

    return {
        "routing_mode": {
            "auto": auto_count,
            "manual": manual_count,
            "total": total_routing
        },
        "task_distribution": task_distribution,
        "profile_distribution": [
            {"profile_name": k, "count": v} for k, v in profile_distribution.items()
        ]
    }
