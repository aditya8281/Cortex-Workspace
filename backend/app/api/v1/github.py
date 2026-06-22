"""GitHub connection endpoint — link/unlink a GitHub account."""

from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.models.user import User

router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────────────


class GitHubConnectRequest(BaseModel):
    username: str
    token: str  # GitHub personal access token


class GitHubResponse(BaseModel):
    connected: bool
    github_username: str | None = None


# ── Endpoints ────────────────────────────────────────────────────────


@router.get("", response_model=GitHubResponse)
async def get_github_status(
    current_user: User = Depends(get_current_user),
):
    """Check if the current user has a GitHub account connected."""
    return GitHubResponse(
        connected=bool(current_user.github_username),
        github_username=current_user.github_username,
    )


@router.post("", response_model=GitHubResponse)
async def connect_github(
    body: GitHubConnectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Connect a GitHub account by storing username + encrypted token."""
    gh_username = body.username.strip()
    if not re.match(r"^[a-zA-Z0-9-]+$", gh_username):
        raise HTTPException(status_code=400, detail="Invalid GitHub username")

    # Check if this GitHub username is already connected to another account
    existing = (
        db.query(User)
        .filter(
            User.github_username == gh_username,
            User.id != current_user.id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="This GitHub account is already connected to another user")

    # Encrypt the token with Fernet so it can be recovered later for API calls
    import base64 as _b64

    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF

    from backend.app.core.config import settings

    # Derive a Fernet key from the app secret using HKDF (deterministic, same across restarts)
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"github-token-encryption",
    )
    key = hkdf.derive(settings.SECRET_KEY.encode())
    fernet_key = Fernet(_b64.urlsafe_b64encode(key))
    encrypted = fernet_key.encrypt(body.token.encode()).decode()

    current_user.github_username = gh_username
    current_user.github_token_encrypted = encrypted
    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return GitHubResponse(connected=True, github_username=gh_username)


@router.delete("", response_model=GitHubResponse)
async def disconnect_github(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Disconnect the current user's GitHub account."""
    current_user.github_username = None
    current_user.github_token_encrypted = None
    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return GitHubResponse(connected=False, github_username=None)
