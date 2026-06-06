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
        # Accept new `data_path` or legacy `personal_storage_path`
        personal_storage = getattr(user, "data_path", None) or getattr(user, "personal_storage_path", None)
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
        # store canonical `data_path` and keep legacy `personal_storage_path` in sync
        data_path=personal_storage,
        personal_storage_path=personal_storage,
        preferences=preferences_val,
    )

    db.add(db_user)
    try:
        db.commit()
        db.refresh(db_user)
    except Exception as e:
        db.rollback()
        logger.exception("Failed to commit new user: %s", e)
        return None

    # Initialize personal storage path for the new user if provided
    if personal_storage:
        try:
            # Register storage entry and create folder structure for user
            from backend.app.services.storage_registry import register_user_storage
            target_path = Path(personal_storage).expanduser().resolve()
            logger.info("Initializing personal storage path: %s", target_path)
            # create registry entry
            register_user_storage(db, db_user.id, str(target_path))

            # create expected folders with safe permissions
            profile_dir = target_path / "profile"
            vault_dir = target_path / "vault"
            exports_dir = target_path / "exports"
            activity_dir = target_path / "activity"
            metadata_dir = target_path / "metadata"
            for d in [profile_dir, vault_dir, exports_dir, activity_dir, metadata_dir]:
                d.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.exception("Failed to initialize personal storage; rolling back user: %s", e)
            # Rollback user creation to keep DB and filesystem consistent
            try:
                db.delete(db_user)
                db.commit()
            except Exception:
                db.rollback()
            return None

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

    # Per new storage model, do not switch system memory on user login.

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
            "data_path": user.data_path,
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
