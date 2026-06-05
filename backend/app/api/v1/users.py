from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.schemas.user import UserResponse, UserUpdate
from backend.app.services.user_service import get_user, get_users, delete_user, update_user, promote_user, demote_user
from backend.app.api.deps import get_current_user, get_db
from backend.app.models.user import User
from backend.app.core.rbac import require_admin, can_modify_self

router = APIRouter()


def check_admin_user(current_user: User = Depends(get_current_user)):
    # Deprecated inline check — keep wrapper for compatibility but delegate to centralized RBAC
    return require_admin(current_user)


@router.get("/users", response_model=list[UserResponse])
def read_users(
    db: Session = Depends(get_db),
    _admin_user: User = Depends(require_admin)
):
    return get_users(db)


@router.get("/users/{user_id}", response_model=UserResponse)
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    _admin_user: User = Depends(require_admin)
):
    user = get_user(db, user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user_endpoint(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    _admin_user: User = Depends(require_admin)
):
    updated_user = update_user(db, user_id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return updated_user


@router.delete("/users/{user_id}")
def delete_user_endpoint(
    user_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    success = delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return {"message": "User deleted successfully"}


@router.post("/users/{user_id}/promote", response_model=UserResponse)
def promote_user_endpoint(user_id: int, db: Session = Depends(get_db), admin_user: User = Depends(require_admin)):
    promoted = promote_user(db, user_id)
    if not promoted:
        raise HTTPException(status_code=404, detail="User not found")
    return promoted


@router.post("/users/{user_id}/demote", response_model=UserResponse)
def demote_user_endpoint(user_id: int, db: Session = Depends(get_db), admin_user: User = Depends(require_admin)):
    try:
        demoted = demote_user(db, user_id, admin_user.id)
    except HTTPException:
        raise
    if not demoted:
        raise HTTPException(status_code=404, detail="User not found")
    return demoted
