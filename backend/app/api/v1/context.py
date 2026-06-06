from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
import uuid
from sqlalchemy.orm import Session
from backend.app.core.db import get_db
from backend.app.services.context_manager import ContextManager
from backend.app.schemas.context_item import AttachContextRequest
from backend.app.models.context_item import ContextItem as DBContextItem

# Create a new router for context endpoints
router = APIRouter()

@router.post("/attach")
async def attach_context(request: AttachContextRequest, db: Session = Depends(get_db)):
    manager = ContextManager(db)
    # Generate a unique ID if not provided by the frontend
    if not request.item.id:
        request.item.id = f"ctx-{uuid.uuid4()}"
    
    # Check if context item already exists to avoid unique constraint violations
    existing = db.query(DBContextItem).filter(DBContextItem.id == request.item.id).first()
    if existing:
        # Update existing
        patch = request.item.model_dump(exclude_unset=True)
        updated = manager.update_context(request.item.id, patch)
        return {"id": request.item.id, "item": updated}

    db_item = manager.attach_context(request.item)
    return {"id": db_item.id, "item": db_item}

@router.delete("/{context_id}")
async def remove_context(context_id: str, db: Session = Depends(get_db)):
    manager = ContextManager(db)
    success = manager.remove_context(context_id)
    if success:
        return {"message": "Context item removed successfully"}
    else:
        raise HTTPException(status_code=404, detail="Context item not found")

@router.patch("/{context_id}")
async def update_context(context_id: str, patch_data: dict, db: Session = Depends(get_db)):
    manager = ContextManager(db)
    updated = manager.update_context(context_id, patch_data)
    if updated:
        return {"message": "Context item updated successfully", "item": updated}
    else:
        raise HTTPException(status_code=404, detail="Context item not found")

@router.get("/")
async def list_context(session_id: Optional[str] = None, db: Session = Depends(get_db)):
    manager = ContextManager(db)
    if session_id:
        return manager.list_context(session_id)
    return db.query(DBContextItem).all()

@router.post("/resolve")
async def resolve_context(context_ids: List[str], db: Session = Depends(get_db)):
    manager = ContextManager(db)
    return manager.resolve_context(context_ids)