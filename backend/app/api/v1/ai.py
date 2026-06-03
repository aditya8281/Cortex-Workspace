from typing import List, Optional
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.ai.gateway import AIGateway
from backend.app.api.deps import get_current_user, get_db
from backend.app.models.user import User
from backend.app.models.user_settings import UserSettings
from backend.app.api.v1.user_settings import decrypt_key
from backend.app.ai.exceptions import ModelNotInstalledError
from backend.app.ai.memory.repository import MemoryRepository

router = APIRouter()
gateway = AIGateway()


class ChatTurn(BaseModel):
    role: str
    content: str


class QueryRequest(BaseModel):
    query: str
    history: Optional[List[ChatTurn]] = None
    llm_model: Optional[str] = None
    embedding_model: Optional[str] = None
    vector_db: Optional[str] = None
    inference_engine: Optional[str] = None
    code_parsing: Optional[str] = None
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None


class AIResponse(BaseModel):
    query: str
    response: str
    user_id: int | None = None
    execution_id: str | None = None
    routing_info: Optional[dict] = None


@router.post("/ask", response_model=AIResponse)
async def ask_public(payload: QueryRequest):
    """
    Public query endpoint. Routes request through the AI Gateway.
    """
    try:
        result = await gateway.route(
            query=payload.query,
            history=payload.history,
            llm_model=payload.llm_model,
            embedding_model=payload.embedding_model,
            vector_db=payload.vector_db,
            inference_engine=payload.inference_engine,
            code_parsing=payload.code_parsing,
            api_key=payload.api_key,
            api_base_url=payload.api_base_url
        )
        return AIResponse(
            query=payload.query,
            response=result.answer,
            execution_id=result.execution_id,
            routing_info=result.routing_info
        )
    except ModelNotInstalledError as e:
        return JSONResponse(
            status_code=422,
            content={"error": "model_not_installed", "model": e.model}
        )


@router.post("/chat", response_model=AIResponse)
async def chat_private(
    payload: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Authenticated chat endpoint. Remembers user context and saves conversation memory.
    """
    api_key = payload.api_key
    api_base_url = payload.api_base_url

    if payload.inference_engine == "API":
        if not api_key or not api_base_url:
            settings_entry = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
            if settings_entry:
                if not api_key:
                    api_key = decrypt_key(settings_entry.api_key_encrypted)
                if not api_base_url:
                    api_base_url = settings_entry.api_base_url

    try:
        result = await gateway.route(
            query=payload.query,
            user_id=current_user.id,
            history=payload.history,
            llm_model=payload.llm_model,
            embedding_model=payload.embedding_model,
            vector_db=payload.vector_db,
            inference_engine=payload.inference_engine,
            code_parsing=payload.code_parsing,
            api_key=api_key,
            api_base_url=api_base_url
        )
        return AIResponse(
            query=payload.query,
            response=result.answer,
            user_id=current_user.id,
            execution_id=result.execution_id,
            routing_info=result.routing_info
        )
    except ModelNotInstalledError as e:
        return JSONResponse(
            status_code=422,
            content={"error": "model_not_installed", "model": e.model}
        )


@router.get("/history")
def get_chat_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """
    Get recent query-response history for the current user.
    """
    repository = MemoryRepository()
    return repository.get_recent_history(user_id=current_user.id, limit=limit)