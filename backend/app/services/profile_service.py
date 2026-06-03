import json

from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.models.user_profile import UserProfile
from backend.app.schemas.profile import UserProfileSchema, UserProfileUpdateSchema


def _loads(raw: str, default: list) -> list:
    try:
        data = json.loads(raw or "[]")
        return data if isinstance(data, list) else default
    except Exception:
        return default


def _completion(profile: UserProfile) -> int:
    fields = [
        profile.display_name,
        profile.bio,
        profile.job_title,
        len(_loads(profile.interests_json, [])) > 0,
        len(_loads(profile.goals_json, [])) > 0,
        len(_loads(profile.focus_areas_json, [])) > 0,
    ]
    done = sum(1 for f in fields if f)
    return round((done / len(fields)) * 100)


def get_or_create(db: Session, user: User) -> UserProfile:
    row = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if row is None:
        row = UserProfile(
            user_id=user.id,
            display_name=user.full_name,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def to_schema(user: User, profile: UserProfile) -> UserProfileSchema:
    return UserProfileSchema(
        display_name=profile.display_name or user.full_name,
        email=user.email,
        job_title=profile.job_title,
        location=profile.location,
        bio=profile.bio,
        interests=_loads(profile.interests_json, []),
        goals=_loads(profile.goals_json, []),
        focus_areas=_loads(profile.focus_areas_json, []),
        primary_languages=_loads(profile.languages_json, []),
        onboarding_completed=profile.onboarding_completed,
        completion_percent=_completion(profile),
    )


def update_profile(db: Session, user: User, payload: UserProfileUpdateSchema) -> UserProfileSchema:
    row = get_or_create(db, user)

    if payload.display_name is not None:
        row.display_name = payload.display_name
    if payload.job_title is not None:
        row.job_title = payload.job_title
    if payload.location is not None:
        row.location = payload.location
    if payload.bio is not None:
        row.bio = payload.bio
    if payload.interests is not None:
        row.interests_json = json.dumps(payload.interests)
    if payload.goals is not None:
        row.goals_json = json.dumps(payload.goals)
    if payload.focus_areas is not None:
        row.focus_areas_json = json.dumps(payload.focus_areas)
    if payload.primary_languages is not None:
        row.languages_json = json.dumps(payload.primary_languages)
    if payload.onboarding_completed is not None:
        row.onboarding_completed = payload.onboarding_completed

    db.commit()
    db.refresh(row)
    return to_schema(user, row)
