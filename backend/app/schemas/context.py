from typing import Optional
from pydantic import BaseModel


class ContextItem(BaseModel):
    """Unified context item used throughout the executor pipeline."""
    id: str
    kind: str  # file, folder, repo, memory, url, terminal
    title: str
    detail: Optional[str] = None
    path: Optional[str] = None
    url: Optional[str] = None
    content_preview: Optional[str] = None
    # Populated by ContextResolver after resolution
    resolved_content: Optional[str] = None
    session_id: Optional[str] = None