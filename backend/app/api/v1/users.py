from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.schemas.user import UserLogin, TokenResponse
from backend.app.services.user_service import login_user
from backend.app.api.deps import get_current_user
from backend.app.models.user import User

from backend.app.api.deps import get_db
from backend.app.schemas.user import UserCreate, UserResponse
from backend.app.services.user_service import (
    create_user,
    get_user,
    get_users
)

router = APIRouter()


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
@router.get("/users", response_model=list[UserResponse])
def read_users(db: Session = Depends(get_db)):
    return get_users(db)


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

@router.post("/login", response_model=TokenResponse)
def login(
    payload: UserLogin,
    db: Session = Depends(get_db)
):
    token = login_user(db, payload.email, payload.password)

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    return token

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name
    }