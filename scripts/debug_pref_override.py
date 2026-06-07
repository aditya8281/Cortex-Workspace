import sys
from pathlib import Path
import tempfile

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.db.base import Base
from backend.app.api.deps import get_db
from backend.app.main import app

# create temp sqlite file
with tempfile.TemporaryDirectory() as td:
    db_file = Path(td) / "test.db"
    db_url = f"sqlite:///{db_file}"
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
        # setup admin and user
        client.post('/api/auth/register', json={
            'username':'dummyadmin4','full_name':'Dummy','nickname':'d','password':'securepassword123','confirm_password':'securepassword123','vault_password':'vaultpassword','personal_storage_path':'~'
        })
        client.post('/api/auth/register', json={
            'username':'profileuser3','full_name':'Profile User','nickname':'prof','password':'initialPass123','confirm_password':'initialPass123','vault_password':'vaultPass','personal_storage_path':'~'
        })
        login = client.post('/api/auth/login', json={'username':'profileuser3','password':'initialPass123'})
        print('login', login.status_code, login.text)
        token = login.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        pref_payload = {"interaction_style":"casual","response_style":"concise"}
        resp = client.put('/api/v1/me/profile/preferences', json=pref_payload, headers=headers)
        print('prefs status', resp.status_code)
        print('prefs body', resp.text)

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
