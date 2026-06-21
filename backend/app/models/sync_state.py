from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func

from backend.app.db.base import Base


class SyncState(Base):
    __tablename__ = "sync_states"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    repo_path = Column(String, nullable=False)
    repo_id = Column(Integer, nullable=True)
    status = Column(String, default="active")
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    files_watched = Column(Integer, default=0)
    files_changed = Column(Integer, default=0)
    error_message = Column(String, nullable=True)
    config_json = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
