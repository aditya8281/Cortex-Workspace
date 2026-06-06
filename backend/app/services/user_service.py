import logging
from pathlib import Path
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.schemas.user import UserCreate, UserUpdate, UserRegisterPayload
from backend.app.core.security import hash_password, verify_password, create_access_token

logger = logging.getLogger(__name__)


def create_user(db: Session, user: UserRegisterPayload | UserCreate) -> User | None:
    existing_username = db.query(User).filter(User.username == user.username).first()
    if existing_username:
        return None

    hashed_pw = hash_password(user.password)

    is_first_user = db.query(User).count() == 0
    assigned_role = "admin" if is_first_user else "user"

    # Handle both new multi-step registration and legacy UserCreate
    if hasattr(user, "vault_password"):
        vault_pw_hash = hash_password(user.vault_password)
        personal_storage = user.personal_storage_path
        nickname_val = user.nickname
        bio_val = user.bio
        description_val = user.description
        profile_photo_val = user.profile_photo
        handles_val = user.handles or {}
        preferences_val = user.preferences or {}
    else:
        vault_pw_hash = None
        personal_storage = None
        nickname_val = user.full_name or user.username
        bio_val = None
        description_val = None
        profile_photo_val = None
        handles_val = {}
        preferences_val = {}

    db_user = User(
        username=user.username,
        full_name=user.full_name or user.username,
        hashed_password=hashed_pw,
        role=assigned_role,
        nickname=nickname_val,
        bio=bio_val,
        description=description_val,
        profile_photo=profile_photo_val,
        handles=handles_val,
        vault_password_hash=vault_pw_hash,
        personal_storage_path=personal_storage,
        preferences=preferences_val,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Initialize personal storage path for the new user if provided
    if personal_storage:
        try:
            from backend.app.services.memory_manager import memory_manager
            target_path = Path(personal_storage).expanduser().resolve()
            logger.info("Initializing personal storage path: %s", target_path)
            memory_manager.change_memory_vault(str(target_path))
        except Exception as e:
            logger.error("Failed to configure personal storage path during registration: %s", e)

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

    # Load custom personal storage path if set and different from current path
    if user.personal_storage_path:
        try:
            from backend.app.services.memory_manager import memory_manager
            current_path = memory_manager.get_memory_path()
            target_path = Path(user.personal_storage_path).expanduser().resolve()
            if current_path != target_path:
                logger.info("Switching memory vault storage to user path: %s", target_path)
                memory_manager.change_memory_vault(str(target_path))
        except Exception as e:
            logger.error("Failed to load user personal storage path during login: %s", e)

    token = create_access_token(data={"sub": str(user.id)})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role,
            "nickname": user.nickname,
            "bio": user.bio,
            "description": user.description,
            "profile_photo": user.profile_photo,
            "handles": user.handles,
            "personal_storage_path": user.personal_storage_path,
            "preferences": user.preferences,
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
