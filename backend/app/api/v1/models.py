import json
import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from backend.app.core.config import settings
from backend.app.api.deps import get_current_user
from backend.app.models.user import User
from backend.app.api.v1.users import check_admin_user

router = APIRouter()


class PullModelPayload(BaseModel):
    model: str


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
    current_user: User = Depends(check_admin_user)
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
