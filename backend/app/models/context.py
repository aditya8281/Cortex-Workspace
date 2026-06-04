from pydantic import BaseModel
from typing import Optional

class ContextItem(BaseModel):
    id: str
    kind: str  # file, folder, repo, memory, url, terminal
    title: str
    detail: Optional[str] = None
    path: Optional[str] = None
    url: Optional[str] = None
    content_preview: Optional[str] = None