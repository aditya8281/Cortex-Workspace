import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

# create admin
client.post('/api/auth/register', json={
    'username':'dummyadmin3','full_name':'Dummy','nickname':'d','password':'securepassword123','confirm_password':'securepassword123','vault_password':'vaultpassword','personal_storage_path':'~'
})
# create user
client.post('/api/auth/register', json={
    'username':'profileuser2','full_name':'Profile User','nickname':'prof','password':'initialPass123','confirm_password':'initialPass123','vault_password':'vaultPass','personal_storage_path':'~'
})
# login
r = client.post('/api/auth/login', json={'username':'profileuser2','password':'initialPass123'})
print('login status', r.status_code, r.text)
token = r.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}
# update prefs
pref_payload = {"interaction_style":"casual","response_style":"concise"}
resp = client.put('/api/v1/me/profile/preferences', json=pref_payload, headers=headers)
print('prefs status', resp.status_code, resp.text)

