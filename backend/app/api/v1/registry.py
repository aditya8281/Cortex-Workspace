"""REST API endpoints for Ollama model registry"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.db.base import get_db
from backend.app.services.ollama_registry import OllamaRegistryService, OllamaDownloadService
from backend.app.core.security import get_current_user

router = APIRouter(prefix="/api/v1/registry", tags=["model-registry"])


@router.get("/sync")
async def sync_registry(
    force_refresh: bool = Query(False, description="Force refresh registry from Ollama library"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Sync Ollama library models with local registry.
    
    Args:
        force_refresh: If True, ignore 24-hour cache and re-scrape
        
    Returns:
        Number of models synced
    """
    try:
        count = await OllamaRegistryService.sync_registry(db, force_refresh=force_refresh)
        return {
            "success": True,
            "models_synced": count,
            "message": f"Registry synced with {count} models",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/models")
async def list_all_models(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Get all models in registry"""
    models = OllamaRegistryService.list_all_models(db)
    return {
        "models": models,
        "total": len(models),
        "source": "ollama-library-cache",
    }


@router.get("/models/installed")
async def list_installed_models(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Get only installed models"""
    models = OllamaRegistryService.list_installed_models(db)
    return {
        "models": models,
        "total": len(models),
    }


@router.get("/models/by-capability/{capability}")
async def list_by_capability(
    capability: str,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Get models with specific capability.
    
    Available capabilities:
    - chat: Conversational AI
    - coding: Code generation and completion
    - vision: Image understanding
    - embedding: Text embeddings
    - reasoning: Advanced reasoning
    - fast: Optimized for speed
    - long-context: Extended context windows
    """
    models = OllamaRegistryService.list_by_capability(db, capability, limit=limit)
    
    if not models:
        return {
            "models": [],
            "total": 0,
            "capability": capability,
            "message": f"No models found with capability '{capability}'",
        }
    
    return {
        "models": models,
        "total": len(models),
        "capability": capability,
    }


@router.get("/models/search")
async def search_models(
    q: str = Query(..., min_length=1, description="Search query"),
    capability: Optional[str] = Query(None, description="Filter by capability"),
    family: Optional[str] = Query(None, description="Filter by model family"),
    size: Optional[str] = Query(None, description="Filter by size: small, medium, large"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Search and filter models.
    
    Examples:
    - /search?q=llama&capability=chat
    - /search?q=code&size=small
    - /search?q=vision
    """
    if size and size.lower() not in ["small", "medium", "large"]:
        raise HTTPException(
            status_code=400,
            detail="size must be 'small', 'medium', or 'large'"
        )
    
    models = OllamaRegistryService.search_models(
        db,
        query=q,
        capability=capability,
        family=family,
        size=size,
        limit=limit,
    )
    
    return {
        "models": models,
        "total": len(models),
        "query": q,
        "filters": {
            "capability": capability,
            "family": family,
            "size": size,
        },
    }


@router.get("/models/{model_id}")
async def get_model(
    model_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Get full metadata for specific model"""
    model = OllamaRegistryService.get_model(db, model_id)
    
    if not model:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")
    
    return {
        "model": model,
    }


@router.post("/models/{model_id}/pull")
async def pull_model(
    model_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Start downloading a model via ollama pull.
    
    Returns a progress_id to track download status.
    """
    # Verify model exists
    model = OllamaRegistryService.get_model(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")
    
    # Start download
    progress_id = await OllamaDownloadService.start_download(db, model_id)
    
    if not progress_id:
        raise HTTPException(status_code=400, detail="Failed to start download")
    
    return {
        "success": True,
        "model_id": model_id,
        "progress_id": progress_id,
        "pull_command": model["pull_command"],
        "message": f"Download started. Use progress_id to track status.",
    }


@router.get("/downloads/{progress_id}")
async def get_download_progress(
    progress_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Get current download progress by progress_id"""
    progress = await OllamaDownloadService.get_download_progress(db, progress_id)
    
    if not progress:
        raise HTTPException(status_code=404, detail="Download progress not found")
    
    return {
        "progress": progress,
    }


@router.get("/recommendations")
async def get_recommendations(
    task: Optional[str] = Query(
        None,
        description="Task type: 'chat', 'coding', 'vision', 'reasoning', 'fast', 'embedding'"
    ),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Get recommended models for specific task.
    
    Available tasks:
    - chat: General conversation
    - coding: Code generation
    - vision: Image understanding
    - reasoning: Complex reasoning
    - fast: Low latency, small models
    - embedding: Text embeddings
    """
    if not task:
        raise HTTPException(
            status_code=400,
            detail="'task' parameter is required"
        )
    
    task_lower = task.lower()
    
    # Map task to capabilities and preferences
    task_config = {
        "chat": {
            "capability": "chat",
            "limit": 10,
        },
        "coding": {
            "capability": "coding",
            "limit": 10,
        },
        "vision": {
            "capability": "vision",
            "limit": 5,
        },
        "reasoning": {
            "capability": "reasoning",
            "limit": 10,
        },
        "fast": {
            "capability": "fast",
            "size": "small",
            "limit": 10,
        },
        "embedding": {
            "capability": "embedding",
            "limit": 5,
        },
    }
    
    if task_lower not in task_config:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown task. Available: {', '.join(task_config.keys())}"
        )
    
    config = task_config[task_lower]
    
    models = OllamaRegistryService.list_by_capability(
        db,
        capability=config["capability"],
        limit=config.get("limit", 10),
    )
    
    # Additional filtering for size if specified
    if "size" in config:
        models = OllamaRegistryService._filter_by_size(
            [m for m in OllamaRegistryService.list_all_models(db) if m in models],
            config["size"]
        )
        models = [OllamaRegistryService._model_to_dict(m) for m in models]
    
    return {
        "task": task,
        "recommendations": models,
        "total": len(models),
        "note": "Models are ranked by relevance for this task",
    }


@router.post("/models/{model_id}/mark-installed")
async def mark_installed(
    model_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Mark a model as installed (for external installation tracking)"""
    success = OllamaRegistryService.mark_installed(db, model_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")
    
    return {
        "success": True,
        "model_id": model_id,
        "message": "Model marked as installed",
    }
