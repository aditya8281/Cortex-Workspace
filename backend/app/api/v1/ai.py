from typing import List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.app.ai.gateway import AIGateway
from backend.app.api.deps import get_current_user
from backend.app.models.user import User
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


class AIResponse(BaseModel):
    query: str
    response: str
    user_id: int | None = None
    execution_id: str | None = None


@router.post("/ask", response_model=AIResponse)
async def ask_public(payload: QueryRequest):
    """
    Public query endpoint. Routes request through the AI Gateway.
    """
    result = await gateway.route(
        query=payload.query,
        history=payload.history,
        llm_model=payload.llm_model,
        embedding_model=payload.embedding_model,
        vector_db=payload.vector_db,
        inference_engine=payload.inference_engine,
        code_parsing=payload.code_parsing
    )
    return AIResponse(
        query=payload.query,
        response=result.answer,
        execution_id=result.execution_id
    )


@router.post("/chat", response_model=AIResponse)
async def chat_private(
    payload: QueryRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Authenticated chat endpoint. Remembers user context and saves conversation memory.
    """
    result = await gateway.route(
        query=payload.query,
        user_id=current_user.id,
        history=payload.history,
        llm_model=payload.llm_model,
        embedding_model=payload.embedding_model,
        vector_db=payload.vector_db,
        inference_engine=payload.inference_engine,
        code_parsing=payload.code_parsing
    )
    return AIResponse(
        query=payload.query,
        response=result.answer,
        user_id=current_user.id,
        execution_id=result.execution_id
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