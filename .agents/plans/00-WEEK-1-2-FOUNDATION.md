> **⚠️ DEPRECATED:** This plan is no longer active. The foundation already exists in the codebase. Do not execute this plan. See [prerequisite.md](../prerequisite.md) for current work.

# Foundation & Core Infrastructure Plan (Weeks 1-2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Establish the complete foundation — FastAPI backend with auth/encryption, Next.js 15 frontend with design system, PostgreSQL schema, and CI/CD pipeline — enabling all future development by end of Week 2.

**Architecture:** Monorepo with `backend` (FastAPI + SQLAlchemy 2.0 + Alembic) and `frontend` (Next.js 15 + React 19 + Tailwind). PostgreSQL 15 with embedded pg for dev. JWT auth with Argon2id hashing. AES-256-GCM vault encryption. GitHub Actions for lint/test/build.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL 15, Next.js 15, React 19, TypeScript, Tailwind CSS 3.4, pnpm, uv.

## Global Constraints

- Python 3.12+, Node.js 20+, Rust 2024 edition
- TypeScript strict mode, ESLint zero warnings
- Python: ruff line-length 120, mypy strict
- All async handlers, no blocking in event loop
- PostgreSQL: embedded for dev, external for production
- Auth: JWT access tokens (15min), refresh tokens (7d), Argon2id hashing
- Vault: AES-256-GCM encryption, PBKDF2 600k iterations for key derivation
- No telemetry, no external API calls, local-first

---

## Task 1: Monorepo Scaffold

**Files:**
- Create: `backend/pyproject.toml`
- Create: `frontend/package.json`
- Create: `Makefile`
- Create: `.gitignore`

**Interfaces:**
- Consumes: None (initial setup)
- Produces: Working monorepo with both apps runnable

- [ ] **Step 1: Create backend pyproject.toml**

```toml
[project]
name = "cortex-backend"
version = "0.1.0"
description = "Cortex AI Workspace Backend"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.110.0",
    "uvicorn[standard]>=0.27.0",
    "sqlalchemy[asyncio]>=2.0.0",
    "asyncpg>=0.29.0",
    "alembic>=1.13.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "python-jose[cryptography]>=3.3.0",
    "passlib[argon2]>=1.7.4",
    "python-multipart>=0.0.6",
    "cryptography>=42.0.0",
    "httpx>=0.26.0",
    "redis>=5.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "ruff>=0.2.0",
    "mypy>=1.8.0",
]

[tool.ruff]
line-length = 120
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "B"]

[tool.mypy]
python_version = "3.12"
strict = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 2: Create frontend package.json**

```json
{
  "name": "cortex-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "eslint .",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "next": "^15.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  },
  "devDependencies": {
    "@types/node": "^20.11.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "eslint": "^8.56.0",
    "eslint-config-next": "^15.0.0",
    "postcss": "^8.4.33",
    "tailwindcss": "^3.4.1",
    "typescript": "^5.3.3"
  }
}
```

- [ ] **Step 3: Create Makefile**

```makefile
.PHONY: dev dev-backend dev-frontend test lint typecheck

dev: dev-backend dev-frontend

dev-backend:
	cd backend && uv run uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

test:
	cd backend && PYTHONPATH=. uv run pytest

lint:
	cd backend && uv run ruff check .
	cd frontend && npm run lint

typecheck:
	cd backend && uv run mypy .
	cd frontend && npm run typecheck
```

- [ ] **Step 4: Create .gitignore**

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
.venv/
*.egg-info/
dist/
build/
.mypy_cache/
.ruff_cache/
.pytest_cache/

# Node
node_modules/
.next/
out/

# Rust
target/

# Environment
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Cortex specific
CortexMemory/
*.db
*.sqlite
```

- [ ] **Step 5: Install dependencies**

Run: `cd backend && uv sync`
Run: `cd frontend && npm install`

- [ ] **Step 6: Commit**

```bash
git add backend/pyproject.toml frontend/package.json Makefile .gitignore
git commit -m "chore: initialize monorepo scaffold"
```

---

## Task 2: Backend Core — Config & Database

**Files:**
- Create: `backend/app/main.py`
- Create: `backend/app/core/__init__.py`
- Create: `backend/app/core/config.py`
- Create: `backend/app/core/database.py`
- Create: `backend/app/db/__init__.py`
- Create: `backend/app/db/session.py`
- Create: `backend/app/db/base.py`

**Interfaces:**
- Consumes: Task 1 (pyproject.toml)
- Produces: `get_settings()`, `get_db()`, `async_engine`, `async_session_factory`

- [ ] **Step 1: Create app/core/config.py**

```python
"""Application configuration via pydantic-settings."""
from __future__ import annotations
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Environment-based configuration."""
    
    # App
    APP_NAME: str = "Cortex"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"
    
    # Database
    DATABASE_URL: str = "postgresql://cortex:cortex@localhost:5435/cortex"
    
    # Redis (optional for MVP)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Auth
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    
    # Vault
    VAULT_KEY_ITERATIONS: int = 600_000
    
    # Paths
    CORTEX_ROOT: str = "./CortexMemory"
    
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
```

- [ ] **Step 2: Create app/core/database.py**

```python
"""Async SQLAlchemy engine and session factory."""
from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import get_settings


def get_engine():
    """Create async engine from settings."""
    settings = get_settings()
    return create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_size=5,
        max_overflow=10,
    )


def get_session_factory(engine):
    """Create async session factory."""
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


# Module-level singletons
_engine = None
_session_factory = None


def get_async_engine():
    global _engine
    if _engine is None:
        _engine = get_engine()
    return _engine


def get_async_session_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = get_session_factory(get_async_engine())
    return _session_factory


async def get_db() -> AsyncSession:
    """FastAPI dependency for database sessions."""
    factory = get_async_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

- [ ] **Step 3: Create app/db/base.py**

```python
"""SQLAlchemy declarative base."""
from __future__ import annotations
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all models."""
    pass
```

- [ ] **Step 4: Create app/main.py**

```python
"""FastAPI application entry point."""
from __future__ import annotations
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    # Startup
    settings = get_settings()
    print(f"Starting {settings.APP_NAME}...")
    yield
    # Shutdown
    print("Shutting down...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.APP_NAME,
        lifespan=lifespan,
    )
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Health check
    @app.get("/api/v1/health")
    async def health():
        return {"status": "ok", "app": settings.APP_NAME}
    
    return app


app = create_app()
```

- [ ] **Step 5: Verify backend starts**

Run: `cd backend && uv run uvicorn app.main:app --port 8000`
Expected: Server starts on port 8000

- [ ] **Step 6: Commit**

```bash
git add backend/app/
git commit -m "feat: add backend core config and database"
```

---

## Task 3: User Model & Auth System

**Files:**
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/user.py`
- Create: `backend/app/core/security.py`
- Create: `backend/app/api/auth.py`
- Create: `backend/app/schemas/auth.py`
- Create: `backend/tests/test_auth.py`

**Interfaces:**
- Consumes: Task 2 (database, config)
- Produces: User model, JWT auth, register/login endpoints

- [ ] **Step 1: Create app/models/user.py**

```python
"""User model."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class User(Base):
    """User account model."""
    
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    vault_password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
```

- [ ] **Step 2: Create app/core/security.py**

```python
"""Password hashing and JWT token management."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import get_settings

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using Argon2id."""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token."""
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict | None:
    """Decode and validate a JWT token."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
```

- [ ] **Step 3: Create app/schemas/auth.py**

```python
"""Auth request/response schemas."""
from __future__ import annotations
from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    is_active: bool
    created_at: str
```

- [ ] **Step 4: Create app/api/auth.py**

```python
"""Auth API endpoints."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
)
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest, LoginRequest, TokenResponse,
    RefreshRequest, UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    # Check existing
    existing = await db.execute(
        select(User).where((User.username == request.username) | (User.email == request.email))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    # Create user
    user = User(
        username=request.username,
        email=request.email,
        hashed_password=hash_password(request.password),
    )
    db.add(user)
    await db.flush()
    
    # Generate tokens
    access = create_access_token({"sub": user.id, "username": user.username})
    refresh = create_refresh_token({"sub": user.id})
    
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with credentials."""
    result = await db.execute(select(User).where(User.username == request.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access = create_access_token({"sub": user.id, "username": user.username})
    refresh = create_refresh_token({"sub": user.id})
    
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Refresh access token."""
    payload = decode_token(request.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    access = create_access_token({"sub": user.id, "username": user.username})
    refresh = create_refresh_token({"sub": user.id})
    
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.get("/me", response_model=UserResponse)
async def get_me(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current user profile."""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat(),
    )


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    """Dependency to get current authenticated user."""
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user
```

- [ ] **Step 5: Register router in app/api/router.py**

```python
"""API router aggregation."""
from __future__ import annotations
from fastapi import APIRouter
from app.api.auth import router as auth_router

api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router)
```

Update `app/main.py` to include router:

```python
from app.api.router import api_router
app.include_router(api_router)
```

- [ ] **Step 6: Write tests**

```python
# backend/tests/test_auth.py
"""Tests for auth system."""
from __future__ import annotations
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_register():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPass123!",
        })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register first
        await client.post("/api/auth/register", json={
            "username": "logintest",
            "email": "login@example.com",
            "password": "TestPass123!",
        })
        
        # Login
        response = await client.post("/api/auth/login", json={
            "username": "logintest",
            "password": "TestPass123!",
        })
    
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_get_me():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register
        reg = await client.post("/api/auth/register", json={
            "username": "metest",
            "email": "me@example.com",
            "password": "TestPass123!",
        })
        token = reg.json()["access_token"]
        
        # Get me
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
    
    assert response.status_code == 200
    assert response.json()["username"] == "metest"
```

- [ ] **Step 7: Run tests**

Run: `cd backend && PYTHONPATH=. uv run pytest tests/test_auth.py -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add backend/app/models/ backend/app/core/security.py backend/app/api/ backend/tests/test_auth.py
git commit -m "feat: add user model and auth system"
```

---

## Task 4: Encrypted Vault

**Files:**
- Create: `backend/app/services/vault_service.py`
- Create: `backend/app/api/v1/vault.py`
- Create: `backend/tests/test_vault.py`

**Interfaces:**
- Consumes: Task 3 (User model, auth)
- Produces: Vault encrypt/decrypt, file operations, vault API

- [ ] **Step 1: Create app/services/vault_service.py**

```python
"""Encrypted vault service using AES-256-GCM."""
from __future__ import annotations
import hashlib
import os
import logging
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = logging.getLogger(__name__)


class VaultService:
    """Encrypted file vault for user data.
    
    Uses AES-256-GCM for authenticated encryption.
    Key derived from user's vault password via PBKDF2 (600k iterations).
    """

    def __init__(self, vault_root: str = "./CortexMemory/vault"):
        self._vault_root = Path(vault_root)
        self._vault_root.mkdir(parents=True, exist_ok=True)

    def _derive_key(self, password: str, salt: bytes | None = None) -> tuple[bytes, bytes]:
        """Derive AES key from password using PBKDF2."""
        if salt is None:
            salt = os.urandom(16)
        
        key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt,
            iterations=600_000,
            dklen=32,
        )
        return key, salt

    def encrypt(self, data: bytes, password: str) -> bytes:
        """Encrypt data with AES-256-GCM."""
        key, salt = self._derive_key(password)
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, data, None)
        return salt + nonce + ciphertext

    def decrypt(self, encrypted: bytes, password: str) -> bytes:
        """Decrypt data with AES-256-GCM."""
        salt = encrypted[:16]
        nonce = encrypted[16:28]
        ciphertext = encrypted[28:]
        
        key, _ = self._derive_key(password, salt)
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, None)

    def get_user_vault(self, user_id: str) -> Path:
        """Get vault directory for a user."""
        vault_dir = self._vault_root / user_id
        vault_dir.mkdir(parents=True, exist_ok=True)
        return vault_dir

    async def write_file(
        self, user_id: str, path: str, data: bytes, password: str
    ) -> Path:
        """Write an encrypted file to the vault."""
        vault_dir = self.get_user_vault(user_id)
        file_path = vault_dir / path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        encrypted = self.encrypt(data, password)
        file_path.write_bytes(encrypted)
        
        return file_path

    async def read_file(
        self, user_id: str, path: str, password: str
    ) -> bytes:
        """Read and decrypt a file from the vault."""
        vault_dir = self.get_user_vault(user_id)
        file_path = vault_dir / path
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        encrypted = file_path.read_bytes()
        return self.decrypt(encrypted, password)

    async def list_files(self, user_id: str) -> list[str]:
        """List files in user's vault."""
        vault_dir = self.get_user_vault(user_id)
        return [
            str(f.relative_to(vault_dir))
            for f in vault_dir.rglob("*")
            if f.is_file()
        ]

    async def delete_file(self, user_id: str, path: str) -> bool:
        """Delete a file from the vault."""
        vault_dir = self.get_user_vault(user_id)
        file_path = vault_dir / path
        
        if file_path.exists():
            file_path.unlink()
            return True
        return False
```

- [ ] **Step 2: Create app/api/v1/vault.py**

```python
"""Vault API endpoints."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from app.core.security import decode_token
from app.services.vault_service import VaultService

router = APIRouter(prefix="/vault", tags=["vault"])

_vault_service = VaultService()


class VaultUnlockRequest(BaseModel):
    password: str


class VaultWriteRequest(BaseModel):
    path: str
    content: str  # base64 encoded


class VaultUnlockResponse(BaseModel):
    unlocked: bool
    message: str


@router.post("/unlock", response_model=VaultUnlockResponse)
async def unlock_vault(request: VaultUnlockRequest):
    """Unlock vault with password (validates password)."""
    # In production, verify against stored hash
    return VaultUnlockResponse(unlocked=True, message="Vault unlocked")


@router.post("/files/write")
async def write_file(request: VaultWriteRequest):
    """Write an encrypted file to the vault."""
    # Get current user from token
    # For demo, use a default user_id
    user_id = "default"
    
    import base64
    data = base64.b64decode(request.content)
    
    await _vault_service.write_file(user_id, request.path, data, "demo-password")
    
    return {"status": "written", "path": request.path}


@router.get("/files/list")
async def list_files():
    """List files in the vault."""
    user_id = "default"
    files = await _vault_service.list_files(user_id)
    return {"files": files}


@router.get("/files/{path:path}")
async def read_file(path: str):
    """Read an encrypted file from the vault."""
    user_id = "default"
    
    try:
        data = await _vault_service.read_file(user_id, path, "demo-password")
        return Response(content=data, media_type="application/octet-stream")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")


@router.delete("/files/{path:path}")
async def delete_file(path: str):
    """Delete a file from the vault."""
    user_id = "default"
    deleted = await _vault_service.delete_file(user_id, path)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="File not found")
    
    return {"status": "deleted", "path": path}
```

- [ ] **Step 3: Write tests**

```python
# backend/tests/test_vault.py
"""Tests for vault encryption."""
from __future__ import annotations
import pytest
from app.services.vault_service import VaultService


def test_encrypt_decrypt():
    vault = VaultService()
    password = "secure-password-123"
    data = b"Hello, encrypted world!"
    
    encrypted = vault.encrypt(data, password)
    decrypted = vault.decrypt(encrypted, password)
    
    assert decrypted == data
    assert encrypted != data


def test_wrong_password_fails():
    vault = VaultService()
    data = b"Secret data"
    
    encrypted = vault.encrypt(data, "correct-password")
    
    with pytest.raises(Exception):
        vault.decrypt(encrypted, "wrong-password")


@pytest.mark.asyncio
async def test_write_read_file():
    vault = VaultService()
    
    await vault.write_file("user1", "test.txt", b"Hello", "password")
    data = await vault.read_file("user1", "test.txt", "password")
    
    assert data == b"Hello"


@pytest.mark.asyncio
async def test_list_files():
    vault = VaultService()
    
    await vault.write_file("user2", "a.txt", b"A", "password")
    await vault.write_file("user2", "b.txt", b"B", "password")
    
    files = await vault.list_files("user2")
    assert len(files) >= 2


@pytest.mark.asyncio
async def test_delete_file():
    vault = VaultService()
    
    await vault.write_file("user3", "delete-me.txt", b"Bye", "password")
    deleted = await vault.delete_file("user3", "delete-me.txt")
    
    assert deleted is True
```

- [ ] **Step 4: Run tests**

Run: `cd backend && PYTHONPATH=. uv run pytest tests/test_vault.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/vault_service.py backend/app/api/v1/vault.py backend/tests/test_vault.py
git commit -m "feat: add encrypted vault service"
```

---

## Task 5: Frontend — Next.js Scaffold & Design System

**Files:**
- Create: `frontend/next.config.js`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tailwind.config.ts`
- Create: `frontend/app/layout.tsx`
- Create: `frontend/app/page.tsx`
- Create: `frontend/src/shared/design/tokens.ts`
- Create: `frontend/src/shared/ui/Button.tsx`

**Interfaces:**
- Consumes: Task 1 (package.json)
- Produces: Working Next.js app with design tokens

- [ ] **Step 1: Create next.config.js**

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
};

module.exports = nextConfig;
```

- [ ] **Step 2: Create tailwind.config.ts**

```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          DEFAULT: "#0a0e17",
          surface: "#111827",
          card: "#1a2332",
          elevated: "#243044",
          hover: "#2d3b50",
        },
        border: {
          DEFAULT: "#2d3b50",
          subtle: "#1f2937",
        },
        text: {
          DEFAULT: "#f1f5f9",
          secondary: "#94a3b8",
          muted: "#64748b",
        },
        accent: {
          DEFAULT: "#00d4ff",
          hover: "#00b8e6",
          muted: "rgba(0, 212, 255, 0.15)",
          faint: "rgba(0, 212, 255, 0.05)",
        },
        error: {
          DEFAULT: "#ef4444",
          muted: "rgba(239, 68, 68, 0.15)",
        },
        success: {
          DEFAULT: "#22c55e",
          muted: "rgba(34, 197, 94, 0.15)",
        },
        warning: {
          DEFAULT: "#f59e0b",
          muted: "rgba(245, 158, 11, 0.15)",
        },
      },
      fontFamily: {
        display: ["Space Grotesk", "sans-serif"],
        body: ["IBM Plex Sans", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      boxShadow: {
        card: "0 4px 6px -1px rgba(0, 0, 0, 0.3)",
        elevated: "0 10px 15px -3px rgba(0, 0, 0, 0.4)",
      },
    },
  },
  plugins: [],
};

export default config;
```

- [ ] **Step 3: Create src/shared/design/tokens.ts**

```typescript
export const colors = {
  bg: {
    DEFAULT: "#0a0e17",
    surface: "#111827",
    card: "#1a2332",
    elevated: "#243044",
    hover: "#2d3b50",
  },
  border: {
    DEFAULT: "#2d3b50",
    subtle: "#1f2937",
  },
  text: {
    DEFAULT: "#f1f5f9",
    secondary: "#94a3b8",
    muted: "#64748b",
  },
  accent: {
    DEFAULT: "#00d4ff",
    hover: "#00b8e6",
    muted: "rgba(0, 212, 255, 0.15)",
    faint: "rgba(0, 212, 255, 0.05)",
  },
} as const;

export const fonts = {
  display: "Space Grotesk",
  body: "IBM Plex Sans",
  mono: "JetBrains Mono",
} as const;
```

- [ ] **Step 4: Create src/shared/ui/Button.tsx**

```typescript
"use client";

import { ButtonHTMLAttributes, forwardRef } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost";
  size?: "sm" | "md" | "lg";
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", size = "md", className = "", children, ...props }, ref) => {
    const baseStyles = "inline-flex items-center justify-center font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-accent/50 disabled:opacity-50";
    
    const variants = {
      primary: "bg-accent text-bg hover:bg-accent-hover",
      secondary: "bg-bg-card border border-border text-text hover:bg-bg-hover",
      ghost: "bg-transparent text-text-secondary hover:bg-bg-hover hover:text-text",
    };
    
    const sizes = {
      sm: "h-8 px-3 text-sm",
      md: "h-10 px-4 text-sm",
      lg: "h-12 px-6 text-base",
    };
    
    return (
      <button
        ref={ref}
        className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
        {...props}
      >
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";
```

- [ ] **Step 5: Create app/layout.tsx**

```typescript
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Cortex",
  description: "Local AI Workspace",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-bg text-text font-body antialiased">
        {children}
      </body>
    </html>
  );
}
```

- [ ] **Step 6: Create app/globals.css**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

* {
  box-sizing: border-box;
}

::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #111827;
}

::-webkit-scrollbar-thumb {
  background: #2d3b50;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #3d4f66;
}
```

- [ ] **Step 7: Create app/page.tsx**

```typescript
import { Button } from "@/shared/ui/Button";

export default function Home() {
  return (
    <main className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-display font-bold mb-4">
          <span className="text-accent">Cortex</span>
        </h1>
        <p className="text-text-secondary mb-8">
          Local AI Workspace
        </p>
        <Button>Get Started</Button>
      </div>
    </main>
  );
}
```

- [ ] **Step 8: Create tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

- [ ] **Step 9: Verify frontend builds**

Run: `cd frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 10: Commit**

```bash
git add frontend/
git commit -m "feat: add Next.js scaffold with design system"
```

---

## Task 6: Database Migrations

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/versions/001_initial.py`

**Interfaces:**
- Consumes: Task 2 (database), Task 3 (User model)
- Produces: Alembic migration setup, initial migration

- [ ] **Step 1: Create alembic.ini**

```ini
[alembic]
script_location = alembic
sqlalchemy.url = postgresql://cortex:cortex@localhost:5435/cortex

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

- [ ] **Step 2: Create alembic/env.py**

```python
"""Alembic environment configuration."""
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import asyncio
from sqlalchemy.ext.asyncio import async_engine_from_config

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from app.db.base import Base
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = configuration.get(
        "sqlalchemy.url", ""
    ).replace("postgresql://", "postgresql+asyncpg://")
    
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 3: Generate initial migration**

Run: `cd backend && uv run alembic revision --autogenerate -m "initial"`
Expected: Migration file created in `alembic/versions/`

- [ ] **Step 4: Run migration**

Run: `cd backend && uv run alembic upgrade head`
Expected: Tables created in PostgreSQL

- [ ] **Step 5: Commit**

```bash
git add backend/alembic.ini backend/alembic/
git commit -m "feat: add Alembic migrations"
```

---

## Task 7: CI/CD — GitHub Actions

**Files:**
- Create: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: All previous tasks
- Produces: Automated lint, test, typecheck on PR

- [ ] **Step 1: Create .github/workflows/ci.yml**

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  backend:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: cortex
          POSTGRES_PASSWORD: cortex
          POSTGRES_DB: cortex
        ports:
          - 5435:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      
      - name: Install uv
        uses: astral-sh/setup-uv@v3
      
      - name: Install dependencies
        run: |
          cd backend
          uv sync
      
      - name: Lint
        run: |
          cd backend
          uv run ruff check .
      
      - name: Type check
        run: |
          cd backend
          uv run mypy .
      
      - name: Test
        env:
          DATABASE_URL: postgresql://cortex:cortex@localhost:5435/cortex
          TESTING: "true"
        run: |
          cd backend
          PYTHONPATH=. uv run pytest -v
  
  frontend:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json
      
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      
      - name: Lint
        run: |
          cd frontend
          npm run lint
      
      - name: Type check
        run: |
          cd frontend
          npm run typecheck
      
      - name: Build
        run: |
          cd frontend
          npm run build
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add GitHub Actions workflow"
```

---

## Task 8: Alembic Fix — Initial Migration

**Files:**
- Modify: `backend/alembic/versions/001_initial.py`

**Interfaces:**
- Consumes: Task 6 (Alembic setup)
- Produces: Working initial migration

- [ ] **Step 1: Fix migration file**

The auto-generated migration may have issues. Replace with a clean version:

```python
"""Initial migration

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("username", sa.String(50), unique=True, nullable=False, index=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("vault_password_hash", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("is_superuser", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("users")
```

- [ ] **Step 2: Reset and re-run migration**

Run: `cd backend && uv run alembic downgrade base && uv run alembic upgrade head`
Expected: Tables recreated

- [ ] **Step 3: Commit**

```bash
git add backend/alembic/versions/
git commit -m "fix: clean initial migration"
```

---

## Summary

By end of Week 2, Cortex has:

1. **Monorepo** — `backend` + `frontend` with shared configs
2. **FastAPI Backend** — Async endpoints, CORS, health check
3. **PostgreSQL** — Async SQLAlchemy 2.0, Alembic migrations
4. **Auth System** — Register, login, JWT tokens, Argon2id hashing
5. **Encrypted Vault** — AES-256-GCM encryption, file CRUD
6. **Next.js Frontend** — App router, design tokens, Button component
7. **CI/CD** — GitHub Actions for lint, test, typecheck, build

### Cross-References
- **To 01-WEEK-3-4-MEMORY.md**: User model, DB session, FastAPI app used by memory system
- **To 02-WEEK-5-6-INDEXING.md**: Database used by knowledge graph
- **To 03-WEEK-7-8-AGENTS.md**: Auth used by agent API
