"""Agent endpoint schemas."""

from __future__ import annotations

from pydantic import BaseModel


class AgentInfo(BaseModel):
    id: int
    name: str
    description: str | None = None
    system_prompt: str
    model_id: str
    tools: str | None = None
    is_active: bool
    created_at: str | None = None
    updated_at: str | None = None


class AgentListResponse(BaseModel):
    agents: list[AgentInfo]


class AgentCreateResponse(BaseModel):
    status: str
    agent: AgentInfo


class AgentGetResponse(BaseModel):
    agent: AgentInfo


class AgentUpdateResponse(BaseModel):
    status: str


class AgentRunInfo(BaseModel):
    id: int
    agent_id: int
    user_id: int
    input: str
    status: str
    output: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class AgentStepInfo(BaseModel):
    id: int
    run_id: int
    step_number: int
    action: str
    input: str | None = None
    output: str | None = None
    status: str
    created_at: str | None = None


class AgentRunCreateResponse(BaseModel):
    status: str
    run_id: int


class AgentRunListResponse(BaseModel):
    runs: list[AgentRunInfo]


class AgentRunGetResponse(BaseModel):
    run: AgentRunInfo
    steps: list[AgentStepInfo]


class AgentRunStatusResponse(BaseModel):
    run_id: int
    status: str


class AgentRunStepsResponse(BaseModel):
    steps: list[AgentStepInfo]


class AgentFeedbackInfo(BaseModel):
    id: int
    rating: int
    comment: str | None = None
    created_at: str | None = None


class AgentFeedbackCreateResponse(BaseModel):
    status: str
    feedback: dict


class AgentFeedbackListResponse(BaseModel):
    feedback: list[AgentFeedbackInfo]
