"""Project index Pydantic schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ProjectIndexResponse(BaseModel):
    """Schema for returning a project index."""

    id: int
    user_id: int
    project_path: str
    project_name: str
    project_type: str | None = None
    frameworks: str | None = None
    configuration: str | None = None
    has_tests: int
    has_ci: int
    has_docker: int
    last_scanned: datetime

    model_config = {"from_attributes": True}
