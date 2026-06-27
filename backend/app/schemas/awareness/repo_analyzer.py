"""Repository index Pydantic schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class RepositoryIndexResponse(BaseModel):
    """Schema for returning a repository index."""

    id: int
    user_id: int
    repo_path: str
    repo_name: str
    languages: str | None = None
    total_files: int
    total_lines: int
    framework: str | None = None
    dependencies: str | None = None
    git_branch: str | None = None
    last_commit_hash: str | None = None
    last_indexed: datetime

    model_config = {"from_attributes": True}
