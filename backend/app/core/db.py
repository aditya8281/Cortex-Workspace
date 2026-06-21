from collections.abc import Generator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.security import is_access_token_revoked, verify_access_token
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

    try:
        payload = jwt.decode(raw_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        jti = payload.get("jti")
        if jti and await is_access_token_revoked(jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired or invalid",
        )

    user = db.query(User).filter(User.id == int(user_id), User.deleted_at.is_(None)).first()

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
    try:
        payload = jwt.decode(raw_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        jti = payload.get("jti")
        if jti and await is_access_token_revoked(jti):
            return None
    except JWTError:
        return None
    return db.query(User).filter(User.id == int(user_id), User.deleted_at.is_(None)).first()
