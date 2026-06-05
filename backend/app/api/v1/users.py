from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.schemas.user import UserLogin, TokenResponse, UserCreate, UserResponse, UserUpdate
from backend.app.services.user_service import login_user, create_user, get_user, get_users, delete_user, update_user
from backend.app.api.deps import get_current_user, get_db
from backend.app.models.user import User

router = APIRouter()


def check_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Admin access required"
        )
    return current_user


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
    return UserResponse.model_validate(db_user)


# -----------------------------
@router.get("/users", response_model=list[UserResponse])
def read_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_users(db)


# -----------------------------
@router.get("/users/{user_id}", response_model=UserResponse)
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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
    admin_user: User = Depends(check_admin_user)
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
    admin_user: User = Depends(check_admin_user)
):
    success = delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return {"message": "User deleted successfully"}

@router.post("/login", response_model=TokenResponse)
def login(
    payload: UserLogin,
    db: Session = Depends(get_db)
):
    token_data = login_user(db, payload.email, payload.password)

    if not token_data:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # Ensure user field is included
    if "user" not in token_data or token_data["user"] is None:
        user = db.query(User).filter(User.email == payload.email).first()
        if user:
            token_data["user"] = {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role
            }
    
    return token_data

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role
    }

from pydantic import BaseModel, EmailStr
from typing import Optional

class MeUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None

@router.put("/me", response_model=UserResponse)
def update_me(
    payload: MeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if payload.email is not None and payload.email != current_user.email:
        # Check conflict
        existing = db.query(User).filter(User.email == payload.email).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        current_user.email = payload.email

    if payload.full_name is not None:
        current_user.full_name = payload.full_name

    if payload.password is not None:
        if len(payload.password) < 8:
            raise HTTPException(
                status_code=400,
                detail="Password must be at least 8 characters long"
            )
        from backend.app.core.security import hash_password
        current_user.hashed_password = hash_password(payload.password)

    db.commit()
    db.refresh(current_user)
    return current_user

