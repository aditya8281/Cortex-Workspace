from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.models.user import User
from backend.app.schemas.profile import UserProfileSchema, UserProfileUpdateSchema
from backend.app.services.profile_service import to_schema, update_profile

router = APIRouter()


@router.get("", response_model=UserProfileSchema)
def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return to_schema(current_user)


@router.put("", response_model=UserProfileSchema)
def update_my_profile(
    payload: UserProfileUpdateSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return update_profile(db, current_user, payload)
