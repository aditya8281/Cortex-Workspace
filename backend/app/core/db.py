from collections.abc import Generator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.app.core.security import verify_access_token
from backend.app.db.session import SessionLocal

oauth2_scheme = HTTPBearer(auto_error=False)
oauth2_scheme_optional = HTTPBearer(auto_error=False)


def _extract_token(request: Request, header_token: HTTPAuthorizationCredentials | None) -> str | None:
    if header_token:
        return header_token.credentials
    return request.cookies.get("cortex_access")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    request: Request,
    token: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    from backend.app.models.user import User

    raw_token = _extract_token(request, token)
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired or invalid",
        )

    try:
        user_id = verify_access_token(raw_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired or invalid",
        )

    user = db.query(User).filter(User.id == int(user_id)).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


async def get_current_user_optional(
    request: Request,
    token: HTTPAuthorizationCredentials | None = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db),
):
    from backend.app.models.user import User

    raw_token = _extract_token(request, token)
    if raw_token is None:
        return None
    try:
        user_id = verify_access_token(raw_token)
    except Exception:
        return None
    return db.query(User).filter(User.id == int(user_id)).first()
