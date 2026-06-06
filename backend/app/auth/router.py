from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db
from backend.app.schemas.user import UserRegisterPayload, UserLogin, TokenResponse, UserResponse
from backend.app.auth import service as auth_service
from backend.app.api.deps import get_current_user

router = APIRouter()


@router.post("/api/auth/register", response_model=TokenResponse)
async def register(payload: UserRegisterPayload, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else None
    result = await auth_service.register_user(db, payload, ip)
    return {
        "access_token": result["access_token"],
        "token_type": "bearer",
        "user": result["user"],
    }


@router.post("/api/auth/login", response_model=TokenResponse)
async def login(payload: UserLogin, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else None
    return await auth_service.login_user_service(db, payload.username, payload.password, ip)


@router.post("/api/auth/refresh", response_model=TokenResponse)
async def refresh(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    refresh_token = body.get("refresh_token")
    ip = request.client.host if request.client else None
    return await auth_service.refresh_tokens(db, refresh_token, ip)


@router.post("/api/auth/logout")
async def logout(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    refresh_token = body.get("refresh_token")
    ip = request.client.host if request.client else None
    await auth_service.logout_user(db, refresh_token, ip)
    return {"message": "Logged out"}


@router.get("/api/auth/me", response_model=UserResponse)
def get_me(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return UserResponse.model_validate(current_user)
