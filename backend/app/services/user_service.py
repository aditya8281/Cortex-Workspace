from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.schemas.user import UserCreate, UserUpdate
from backend.app.core.security import hash_password, verify_password, create_access_token


def create_user(db: Session, user: UserCreate):
    existing_username = db.query(User).filter(User.username == user.username).first()
    if existing_username:
        return None

    hashed_pw = hash_password(user.password)

    full_name_value = user.full_name or user.username
    is_first_user = db.query(User).count() == 0
    assigned_role = "admin" if is_first_user else "user"

    db_user = User(
        username=user.username,
        full_name=full_name_value,
        hashed_password=hashed_pw,
        role=assigned_role,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


def get_user(db: Session, user_id: int):
    """Get a user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    """Get all users with pagination."""
    return db.query(User).offset(skip).limit(limit).all()


def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()

    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user


def login_user(db: Session, username: str, password: str):
    user = authenticate_user(db, username, password)

    if not user:
        return None

    token = create_access_token(data={"sub": str(user.id)})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role,
        }
    }


def delete_user(db: Session, user_id: int) -> bool:
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        return False
    db.delete(db_user)
    db.commit()
    return True


def update_user(db: Session, user_id: int, user_update: UserUpdate) -> User | None:
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        return None
    if user_update.username is not None:
        db_user.username = user_update.username
    if user_update.full_name is not None:
        db_user.full_name = user_update.full_name
    if user_update.role is not None and user_update.role != db_user.role:
        raise HTTPException(status_code=400, detail="Role changes are not allowed")
    db.commit()
    db.refresh(db_user)
    return db_user


def promote_user(db: Session, target_user_id: int) -> User | None:
    db_user = db.query(User).filter(User.id == target_user_id).first()
    if not db_user:
        return None
    if db_user.role == "admin":
        return db_user
    db_user.role = "admin"
    db.commit()
    db.refresh(db_user)
    return db_user


def demote_user(db: Session, target_user_id: int, acting_user_id: int) -> User | None:
    db_user = db.query(User).filter(User.id == target_user_id).first()
    if not db_user:
        return None
    # Prevent self-demotion
    if db_user.id == acting_user_id:
        raise HTTPException(status_code=400, detail="Admins cannot demote themselves")
    db_user.role = "user"
    db.commit()
    db.refresh(db_user)
    return db_user
