from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db
from backend.app.schemas.user import UserCreate, UserResponse
from backend.app.services.user_service import (
    create_user,
    get_user,
    get_users
)

router = APIRouter()


# -----------------------------
# Create User (REGISTER)
# -----------------------------
@router.post("/users", response_model=UserResponse)
def create_new_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    db_user = create_user(db, user)

    if not db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    return db_user


# -----------------------------
# Get All Users
# -----------------------------
@router.get("/users", response_model=list[UserResponse])
def read_users(db: Session = Depends(get_db)):
    return get_users(db)


# -----------------------------
# Get Single User
# -----------------------------
@router.get("/users/{user_id}", response_model=UserResponse)
def read_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    user = get_user(db, user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user