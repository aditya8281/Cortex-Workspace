from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.main import app
from backend.app.db.base import Base
from backend.app.api.deps import get_db

# Setup isolated DB
from pathlib import Path
import tempfile

tmpfile = Path("/tmp/debug_pref.db")
try:
    tmpfile.unlink()
except Exception:
    pass

db_url = f"sqlite:///{tmpfile}"
engine = create_engine(db_url, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

with TestClient(app) as client:
    # register admin
    client.post("/api/auth/register", json={
        "username": "dummyadmin",
        "full_name": "Dummy Admin",
        "nickname": "dummy",
        "password": "securepassword123",
        "confirm_password": "securepassword123",
        "vault_password": "vaultpassword123",
        "personal_storage_path": "~/CortexVaultTest"
    })
    # register profileuser
    payload = {
        "username": "profileuser",
        "full_name": "Profile User",
        "nickname": "prof",
        "password": "initialPass123",
        "confirm_password": "initialPass123",
        "vault_password": "vaultPass123",
        "personal_storage_path": "~/CortexVaultTestP"
    }
    reg = client.post("/api/auth/register", json=payload)
    print('reg', reg.status_code, reg.text)
    login_resp = client.post("/api/auth/login", json={"username": "profileuser", "password": "initialPass123"})
    print('login', login_resp.status_code, login_resp.text)
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    pref_payload = {"interaction_style": "casual", "response_style": "concise"}
    r = client.put("/api/v1/me/profile/preferences", json=pref_payload, headers=headers)
    print('prefs status', r.status_code)
    try:
        print('prefs body', r.json())
    except Exception as e:
        print('prefs text', r.text)

app.dependency_overrides.clear()

