from unittest.mock import AsyncMock, MagicMock, patch

HEADERS = {"Authorization": "Bearer fake-token"}


def test_list_repos_empty(client, mock_auth):
    resp = client.get("/api/v1/repos", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["repos"] == []


def test_create_repo(client, mock_auth):
    mock_path = MagicMock()
    mock_path.expanduser.return_value = mock_path
    mock_path.resolve.return_value = mock_path
    mock_path.is_dir.return_value = True
    mock_path.__str__ = MagicMock(return_value="/fake/repo")

    with patch("pathlib.Path", return_value=mock_path):
        resp = client.post(
            "/api/v1/repos",
            json={"name": "Test Repo", "path": "/fake/repo"},
            headers=HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "created"
        assert data["repo"]["repo_name"] == "Test Repo"


def test_get_repo(client, mock_auth, db_session):
    from backend.app.models.awareness.repo_index import RepoIndex

    repo = RepoIndex(
        user_id=1,
        repo_path="/test/repo",
        repo_name="Get Repo",
        status="pending",
    )
    db_session.add(repo)
    db_session.commit()
    db_session.refresh(repo)

    resp = client.get(f"/api/v1/repos/{repo.id}", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["repo"]["id"] == repo.id
    assert data["repo"]["repo_name"] == "Get Repo"


def test_get_repo_not_found(client, mock_auth):
    resp = client.get("/api/v1/repos/99999", headers=HEADERS)
    assert resp.status_code == 404


def test_update_repo(client, mock_auth, db_session):
    from backend.app.models.awareness.repo_index import RepoIndex

    repo = RepoIndex(
        user_id=1,
        repo_path="/test/repo",
        repo_name="Old Name",
        status="pending",
    )
    db_session.add(repo)
    db_session.commit()
    db_session.refresh(repo)

    resp = client.put(
        f"/api/v1/repos/{repo.id}",
        json={"name": "New Name"},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "updated"
    assert data["repo"]["repo_name"] == "New Name"


def test_delete_repo(client, mock_auth, db_session):
    from backend.app.models.awareness.repo_index import RepoIndex

    repo = RepoIndex(
        user_id=1,
        repo_path="/test/repo",
        repo_name="Delete Repo",
        status="pending",
    )
    db_session.add(repo)
    db_session.commit()
    db_session.refresh(repo)

    resp = client.delete(f"/api/v1/repos/{repo.id}", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["status"] == "deleted"

    resp2 = client.get(f"/api/v1/repos/{repo.id}", headers=HEADERS)
    assert resp2.status_code == 404


def test_delete_repo_not_found(client, mock_auth):
    resp = client.delete("/api/v1/repos/99999", headers=HEADERS)
    assert resp.status_code == 404


def test_index_repo(client, mock_auth, db_session):
    from backend.app.models.awareness.repo_index import RepoIndex

    repo = RepoIndex(
        user_id=1,
        repo_path="/test/repo",
        repo_name="Index Repo",
        status="pending",
    )
    db_session.add(repo)
    db_session.commit()
    db_session.refresh(repo)

    with patch("backend.app.api.v1.awareness.repository.enqueue_task", new_callable=AsyncMock) as mock_enqueue:
        mock_enqueue.return_value = "job-123"
        resp = client.post(f"/api/v1/repos/{repo.id}/index", headers=HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "queued"
        assert data["job_id"] == "job-123"


def test_get_repo_status(client, mock_auth, db_session):
    from backend.app.models.awareness.repo_index import RepoIndex

    repo = RepoIndex(
        user_id=1,
        repo_path="/test/repo",
        repo_name="Status Repo",
        status="indexed",
        total_files=10,
        total_chunks=50,
    )
    db_session.add(repo)
    db_session.commit()
    db_session.refresh(repo)

    resp = client.get(f"/api/v1/repos/{repo.id}/status", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["repo_id"] == repo.id
    assert data["status"] == "indexed"
    assert data["total_files"] == 10
    assert data["total_chunks"] == 50


def test_get_repo_graph(client, mock_auth, db_session):
    from backend.app.models.awareness.repo_index import RepoIndex

    repo = RepoIndex(
        user_id=1,
        repo_path="/test/repo",
        repo_name="Graph Repo",
        status="indexed",
    )
    db_session.add(repo)
    db_session.commit()
    db_session.refresh(repo)

    mock_builder = MagicMock()
    mock_builder.get_graph.return_value = {"nodes": [], "edges": []}

    with patch("backend.app.api.v1.awareness.repository.GraphBuilder", return_value=mock_builder):
        resp = client.get(f"/api/v1/repos/{repo.id}/graph", headers=HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert "nodes" in data
        assert "edges" in data
