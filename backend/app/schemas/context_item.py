from typing import Optional
from pydantic import BaseModel


class ContextItem(BaseModel):
    id: str
    kind: str  # file, folder, repo, memory, url, terminal
    title: str
    detail: Optional[str] = None
    path: Optional[str] = None
    url: Optional[str] = None
    content_preview: Optional[str] = None
    # session_id is optional — the frontend may not always send it
    session_id: Optional[str] = None


class AttachContextRequest(BaseModel):
    item: ContextItem