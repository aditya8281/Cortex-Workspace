"""Vault endpoint schemas."""

from __future__ import annotations

from pydantic import BaseModel


class VaultLockResponse(BaseModel):
    locked: bool
    message: str


class VaultStatusResponse(BaseModel):
    locked: bool
    has_vault_password: bool


class VaultFileInfo(BaseModel):
    name: str
    path: str
    is_dir: bool
    size: int | None = None
    modified_at: str | None = None
    created_at: str | None = None


class VaultFileListResponse(BaseModel):
    files: list[VaultFileInfo]


class VaultUploadResponse(BaseModel):
    path: str
    name: str
    size: int


class VaultDeleteResponse(BaseModel):
    deleted: bool


class VaultRenameResponse(BaseModel):
    path: str
    name: str


class VaultMoveResponse(BaseModel):
    source_path: str
    destination_path: str


class VaultMetadataResponse(BaseModel):
    path: str
    favorite: bool | None = None
    tags: list[str] | None = None


class VaultFolderResponse(BaseModel):
    path: str
    name: str


class VaultSearchResult(BaseModel):
    name: str
    path: str
    is_dir: bool
    score: float


class VaultSearchResponse(BaseModel):
    results: list[VaultSearchResult]


class VaultExportResponse(BaseModel):
    exported: int
    destination_dir: str


class VaultChangePasswordResponse(BaseModel):
    message: str
