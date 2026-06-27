"""Repository endpoint schemas."""

from __future__ import annotations

from pydantic import BaseModel


class RepoInfo(BaseModel):
    id: int
    user_id: int
    repo_path: str
    repo_name: str
    primary_language: str | None = None
    total_files: int
    total_chunks: int
    last_indexed_at: str | None = None
    status: str
    created_at: str | None = None
    updated_at: str | None = None


class RepoListResponse(BaseModel):
    repos: list[RepoInfo]


class RepoCreateResponse(BaseModel):
    status: str
    repo: RepoInfo


class RepoGetResponse(BaseModel):
    repo: RepoInfo


class RepoUpdateResponse(BaseModel):
    status: str
    repo: RepoInfo


class RepoDeleteResponse(BaseModel):
    status: str


class IndexResult(BaseModel):
    status: str = "completed"
    files_scanned: int
    files_indexed: int
    files_skipped: int
    chunks_created: int


class RepoIndexResponse(BaseModel):
    status: str
    job_id: str | None = None
    result: IndexResult | None = None


class RepoIndexStatusResponse(BaseModel):
    repo_id: int
    status: str
    total_files: int
    total_chunks: int
    indexed_files: int
    indexed: int
    pending: int
    errors: int
    last_indexed_at: str | None = None


class GraphBuildResponse(BaseModel):
    status: str
    nodes_created: int
    edges_created: int


class GraphGetResponse(BaseModel):
    nodes: list[dict]
    edges: list[dict]


class NodeContextResponse(BaseModel):
    node_id: int
    label: str
    node_type: str
    neighbors: list[dict]
