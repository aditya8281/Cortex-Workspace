"""API integration tests for execution domain — tools and workflows."""

import pytest

HEADERS = {"Authorization": "Bearer fake-token"}


@pytest.mark.usefixtures("client", "mock_auth")
class TestToolsAPI:
    def test_list_tools(self, client):
        response = client.get("/api/v1/tools/list", headers=HEADERS)
        assert response.status_code == 200
        tools = response.json()
        assert isinstance(tools, list)

    def test_get_stats(self, client):
        response = client.get("/api/v1/tools/stats", headers=HEADERS)
        assert response.status_code == 200
        stats = response.json()
        assert "total" in stats
        assert "success_rate" in stats

    def test_execute_tool_not_found(self, client):
        response = client.post(
            "/api/v1/tools/execute",
            json={"tool_name": "nonexistent_tool", "parameters": {}},
            headers=HEADERS,
        )
        assert response.status_code == 404


@pytest.mark.usefixtures("client", "mock_auth")
class TestWorkflowsAPI:
    def test_create_workflow(self, client):
        response = client.post(
            "/api/v1/workflows/create",
            json={
                "name": "Test WF",
                "steps": [{"tool": "echo", "params": {"message": "hi"}}],
            },
            headers=HEADERS,
        )
        assert response.status_code == 200
        wf = response.json()
        assert wf["name"] == "Test WF"
        assert wf["status"] == "idle"
        assert len(wf["steps"]) == 1

    def test_list_workflows(self, client):
        client.post(
            "/api/v1/workflows/create",
            json={
                "name": "List WF",
                "steps": [{"tool": "echo", "params": {}}],
            },
            headers=HEADERS,
        )
        response = client.get("/api/v1/workflows/list", headers=HEADERS)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_workflow(self, client):
        r = client.post(
            "/api/v1/workflows/create",
            json={
                "name": "Get WF",
                "steps": [{"tool": "echo", "params": {}}],
            },
            headers=HEADERS,
        )
        wf_id = r.json()["id"]
        response = client.get(f"/api/v1/workflows/{wf_id}", headers=HEADERS)
        assert response.status_code == 200
        assert response.json()["id"] == wf_id

    def test_cancel_workflow(self, client):
        r = client.post(
            "/api/v1/workflows/create",
            json={
                "name": "Cancel WF",
                "steps": [{"tool": "echo", "params": {}}],
            },
            headers=HEADERS,
        )
        wf_id = r.json()["id"]
        response = client.post(f"/api/v1/workflows/{wf_id}/cancel", headers=HEADERS)
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"

    def test_duplicate_workflow(self, client):
        r = client.post(
            "/api/v1/workflows/create",
            json={
                "name": "Original WF",
                "steps": [{"tool": "echo", "params": {"message": "hi"}}],
            },
            headers=HEADERS,
        )
        wf_id = r.json()["id"]
        response = client.post(
            f"/api/v1/workflows/{wf_id}/duplicate?new_name=Copied+WF",
            headers=HEADERS,
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Copied WF"
        assert len(response.json()["steps"]) == 1

    def test_create_workflow_invalid_tool(self, client):
        response = client.post(
            "/api/v1/workflows/create",
            json={
                "name": "Bad WF",
                "steps": [{"tool": "nonexistent_tool", "params": {}}],
            },
            headers=HEADERS,
        )
        # Tool validation happens at run time, not creation
        assert response.status_code == 200
