from sqlalchemy.orm import Session
from backend.app.models.context_item import ContextItem as DBContextItem
from backend.app.schemas.context import ContextItem
from typing import List

class ContextManager:
    def __init__(self, db: Session):
        self.db = db

    def attach_context(self, context_item: ContextItem) -> DBContextItem:
        db_context_item = DBContextItem(
            id=context_item.id,
            session_id=context_item.session_id,
            kind=context_item.kind,
            title=context_item.title,
            detail=context_item.detail,
            path=context_item.path,
            url=context_item.url,
            content_preview=context_item.content_preview
        )
        self.db.add(db_context_item)
        self.db.commit()
        self.db.refresh(db_context_item)
        return db_context_item

    def remove_context(self, context_id: str) -> bool:
        context_item = self.db.query(DBContextItem).filter(DBContextItem.id == context_id).first()
        if context_item:
            self.db.delete(context_item)
            self.db.commit()
            return True
        return False

    def update_context(self, context_id: str, patch: dict) -> DBContextItem | None:
        context_item = self.db.query(DBContextItem).filter(DBContextItem.id == context_id).first()
        if context_item:
            for key, val in patch.items():
                if hasattr(context_item, key):
                    setattr(context_item, key, val)
            self.db.commit()
            self.db.refresh(context_item)
            return context_item
        return None

    def list_context(self, session_id: str) -> List[DBContextItem]:
        return self.db.query(DBContextItem).filter(DBContextItem.session_id == session_id).all()

    def resolve_context(self, context_ids: List[str]) -> List[DBContextItem]:
        return self.db.query(DBContextItem).filter(DBContextItem.id.in_(context_ids)).all()