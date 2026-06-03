from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.app.ai.gateway import AIGateway
from backend.app.api.deps import get_current_user
from backend.app.models.user import User

router = APIRouter()
gateway = AIGateway()


class QueryRequest(BaseModel):
    query: str


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
    result = await gateway.route(payload.query)
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
    result = await gateway.route(payload.query, user_id=current_user.id)
    return AIResponse(
        query=payload.query,
        response=result.answer,
        user_id=current_user.id,
        execution_id=result.execution_id
    )