from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CreateConversationRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    repo_id: int | None = None


class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    model: str | None = None


class ConversationMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    thinking_content: str | None = None
    tokens: int
    created_at: datetime | None = None


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    repo_id: int | None = None
    model_used: str | None = None
    message_count: int
    total_tokens: int
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ConversationDetailResponse(ConversationResponse):
    messages: list[ConversationMessageResponse] = []


class ConversationListResponse(BaseModel):
    conversations: list[ConversationResponse]
    total: int
