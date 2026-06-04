from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.db.base import Base
from datetime import datetime

class ContextItem(Base):
    __tablename__ = "context_items"

    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, index=True)
    kind = Column(String, index=True)  # file, folder, repo, memory, url, terminal
    title = Column(String)
    detail = Column(Text, nullable=True)
    path = Column(String, nullable=True)
    url = Column(String, nullable=True)
    content_preview = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)