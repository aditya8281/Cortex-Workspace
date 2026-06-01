from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.schemas.user import UserCreate
from backend.app.core.security import hash_password


def create_user(db: Session, user: UserCreate):
    hashed_pw = hash_password(user.password)

    db_user = User(
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_pw
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user