import json
import httpx
import logging
import keyring
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List

from backend.app.core.config import settings
from backend.app.api.deps import get_current_user, get_db
from backend.app.models.user import User
from backend.app.models.llm_model import CortexProvider, CortexModel, CortexRoutingProfile, CortexTaskRoute
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
    is_enabled: bool = True
    is_custom: bool = False


class ValidatePayload(BaseModel):
    name: str
    base_url: str
    api_key: str


class SelectModelPayload(BaseModel):
    model_name: str
    session_id: Optional[str] = None


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
        is_custom=payload.is_custom
    )
    db.add(provider)
    db.commit()
    db.refresh(provider)

    # 3. If validated, fetch models and register them
    if payload.is_enabled and payload.base_url and payload.api_key:
        val_res = await ModelRegistry.validate_provider(payload.name, payload.base_url, payload.api_key)
        for model_name in val_res.get("models", []):
            model = CortexModel(
                name=model_name,
                provider_name=provider.name,
                status="active",
                is_local=False,
                is_custom=True
            )
            db.add(model)
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
    provider.is_enabled = payload.is_enabled
    db.commit()

    # Register models if enabled
    if payload.is_enabled and api_key_to_use:
        base_url_to_use = provider.base_url or ""
        val_res = await ModelRegistry.validate_provider(provider.name, base_url_to_use, api_key_to_use)
        # Clear old models for this provider
        db.query(CortexModel).filter(CortexModel.provider_name == provider.name, CortexModel.is_local.is_(False)).delete()
        for model_name in val_res.get("models", []):
            model = CortexModel(
                name=model_name,
                provider_name=provider.name,
                status="active",
                is_local=False,
                is_custom=True
            )
            db.add(model)
        db.commit()

    return {"message": "Provider updated successfully"}


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
def select_model(payload: SelectModelPayload):
    """
    Select model for current session.
    """
    # Simply echo or persist state ( ZUSTAND client-side remembers state )
    return {"status": "success", "selected_model": payload.model_name}


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
def get_routing_profiles(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
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
def get_routing_routes(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
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
