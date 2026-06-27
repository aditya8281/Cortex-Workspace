import logging
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.security import hash_password, verify_password
from backend.app.models.interaction.user import User
from backend.app.schemas.user import UserCreate, UserRegisterPayload, UserResponse, UserUpdate

logger = logging.getLogger(__name__)


def to_user_response(db: Session, user: User) -> UserResponse:
    """Serialize a User ORM object to a UserResponse with storage_root."""
    from backend.app.services.memory.storage_registry import get_registry_for_user

    registry = get_registry_for_user(db, user.id)
    response = UserResponse.model_validate(user)
    return response.model_copy(update={"storage_root": registry.storage_root if registry else None})


def serialize_user(db: Session, user: User) -> dict:
    """Legacy dict serializer — prefer to_user_response() for new code."""
    return to_user_response(db, user).model_dump()


def _normalize_username(username: str) -> str:
    """Normalize usernames for storage and comparison: strip and lowercase."""
    return (username or "").strip().lower()


def create_user(db: Session, user: UserRegisterPayload | UserCreate) -> User | None:
    normalized = _normalize_username(user.username)
    existing_username = db.query(User).filter(User.username == normalized).first()
    if existing_username:
        return None

    hashed_pw = hash_password(user.password)

    is_first_user = db.query(User).count() == 0
    assigned_role = "admin" if is_first_user else "user"

    if isinstance(user, UserRegisterPayload):
        vault_pw_hash = hash_password(user.vault_password)
        nickname_val = user.nickname
        bio_val = user.bio
        description_val = user.description
        profile_photo_val = user.profile_photo
        handles_val = user.handles or {}
        preferences_val = user.preferences or {}
    else:
        vault_pw_hash = None
        nickname_val = user.full_name or user.username
        bio_val = None
        description_val = None
        profile_photo_val = None
        handles_val = {}
        preferences_val = {}

    db_user = User(
        username=normalized,
        full_name=user.full_name or user.username,
        hashed_password=hashed_pw,
        role=assigned_role,
        nickname=nickname_val,
        bio=bio_val,
        description=description_val,
        profile_photo=profile_photo_val,
        handles=handles_val,
        vault_password_hash=vault_pw_hash,
        preferences=preferences_val,
    )

    db.add(db_user)
    try:
        db.commit()
        db.refresh(db_user)
    except IntegrityError as e:
        db.rollback()
        logger.warning("Duplicate user or constraint violation: %s", e)
        return None
    except Exception as e:
        db.rollback()
        logger.exception("Unexpected error committing new user: %s", e)
        raise

    return db_user


def get_user(db: Session, user_id: int):
    """Get a user by ID (excludes soft-deleted)."""
    return db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    """Get all active users with pagination (excludes soft-deleted)."""
    return db.query(User).filter(User.deleted_at.is_(None)).offset(skip).limit(limit).all()


def authenticate_user(db: Session, username: str, password: str):
    normalized = _normalize_username(username)
    user = db.query(User).filter(User.username == normalized, User.deleted_at.is_(None)).first()

    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user


def delete_user(db: Session, user_id: int) -> bool:
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        return False
    db_user.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return True


def restore_user(db: Session, user_id: int) -> bool:
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user or not db_user.deleted_at:
        return False
    db_user.deleted_at = None
    db.commit()
    return True


def update_user(db: Session, user_id: int, user_update: UserUpdate) -> User | None:
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        return None
    if user_update.username is not None:
        db_user.username = _normalize_username(user_update.username)
    if user_update.full_name is not None:
        db_user.full_name = user_update.full_name
    if user_update.role is not None and user_update.role != db_user.role:
        raise HTTPException(status_code=400, detail="Role changes are not allowed")
    db.commit()
    db.refresh(db_user)
    return db_user


def promote_user(db: Session, target_user_id: int) -> User | None:
    db_user = db.query(User).filter(User.id == target_user_id, User.deleted_at.is_(None)).first()
    if not db_user:
        return None
    if db_user.role == "admin":
        return db_user
    db_user.role = "admin"
    db.commit()
    db.refresh(db_user)
    return db_user


def demote_user(db: Session, target_user_id: int, acting_user_id: int) -> User | None:
    db_user = db.query(User).filter(User.id == target_user_id, User.deleted_at.is_(None)).first()
    if not db_user:
        return None
    if db_user.id == acting_user_id:
        raise HTTPException(status_code=400, detail="Admins cannot demote themselves")
    db_user.role = "user"
    db.commit()
    db.refresh(db_user)
    return db_user
