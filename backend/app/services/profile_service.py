from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.schemas.profile import UserProfileSchema, UserProfileUpdateSchema


def to_schema(user: User) -> UserProfileSchema:
    return UserProfileSchema(
        full_name=user.full_name,
        nickname=user.nickname,
        bio=user.bio,
        description=user.description,
        profile_photo=user.profile_photo,
        handles=user.handles,
    )


def update_profile(db: Session, user: User, payload: UserProfileUpdateSchema) -> UserProfileSchema:
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.nickname is not None:
        user.nickname = payload.nickname
    if payload.bio is not None:
        user.bio = payload.bio
    if payload.description is not None:
        user.description = payload.description
    if payload.profile_photo is not None:
        user.profile_photo = payload.profile_photo
    if payload.handles is not None:
        user.handles = payload.handles

    db.commit()
    db.refresh(user)
    return to_schema(user)
