"""Agent endpoint schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AgentInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    system_prompt: str
    model_id: str
    tools: list[str] | None = Field(default=None, serialization_alias="tools_json")
    is_active: bool
    created_at: str | None = None
    updated_at: str | None = None

    @field_validator("tools", mode="before")
    @classmethod
    def parse_tools(cls, v):
        if isinstance(v, str):
            try:
                import json
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return None
        return v


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
    model_config = ConfigDict(from_attributes=True)

    id: int
    agent_id: int
    user_id: int
    input: str = Field(serialization_alias="input_text")
    status: str
    output: str | None = None
    error: str | None = None
    completed_at: datetime | None = None
    created_at: str | None = None


class AgentStepInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_id: int
    step_number: int
    action: str
    thought: str | None = None
    action_input: dict | None = Field(default=None, serialization_alias="action_input_json")
    observation: str | None = None
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
