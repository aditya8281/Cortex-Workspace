from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.app.api.deps import get_db
from backend.app.services.hierarchical_indexing import HierarchicalIndexingService

router = APIRouter()
indexing_service = HierarchicalIndexingService()


class RepoIndexRequest(BaseModel):
    repo_path: str


class FileIndexRequest(BaseModel):
    file_path: str
    repo_path: str


@router.post("/repo")
async def index_repo(request: RepoIndexRequest, db: Session = Depends(get_db)):
    try:
        node = await indexing_service.index_repo(request.repo_path, db)
        if not node:
            raise HTTPException(status_code=400, detail="Failed to index repository. Path might not exist or be invalid.")
        return {
            "status": "success",
            "message": f"Successfully indexed repository: {request.repo_path}",
            "repo_node_id": node.id,
            "summary": node.content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/file")
async def index_file(request: FileIndexRequest, db: Session = Depends(get_db)):
    try:
        node = await indexing_service.index_file(request.file_path, request.repo_path, db)
        if not node:
            raise HTTPException(status_code=400, detail="Failed to index file. Path might not exist.")
        return {
            "status": "success",
            "message": f"Successfully indexed file: {request.file_path}",
            "file_node_id": node.id,
            "summary": node.content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_memory(query: str, top_k: int = 5, db: Session = Depends(get_db)):
    try:
        results = await indexing_service.search(query, db, top_k=top_k)
        return {
            "query": query,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
