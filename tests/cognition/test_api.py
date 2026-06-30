"""API integration tests for cognition domain — planning, errors, hypothesis, confidence."""

import pytest

HEADERS = {"Authorization": "Bearer fake-token"}


@pytest.mark.usefixtures("client", "mock_auth")
class TestPlanningAPI:
    def test_create_plan(self, client):
        response = client.post("/api/v1/planning/plan", json={"goal": "Test goal"}, headers=HEADERS)
        assert response.status_code == 200
        plan = response.json()
        assert plan["goal"] == "Test goal"
        assert plan["status"] == "active"
        assert len(plan["steps"]) > 0

    def test_get_plan(self, client):
        r = client.post("/api/v1/planning/plan", json={"goal": "Get test"}, headers=HEADERS)
        plan_id = r.json()["id"]
        response = client.get(f"/api/v1/planning/plan/{plan_id}", headers=HEADERS)
        assert response.status_code == 200
        assert response.json()["id"] == plan_id

    def test_get_plan_not_found(self, client):
        response = client.get("/api/v1/planning/plan/99999", headers=HEADERS)
        assert response.status_code == 404

    def test_list_plans(self, client):
        client.post("/api/v1/planning/plan", json={"goal": "List test"}, headers=HEADERS)
        response = client.get("/api/v1/planning/plans", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total"] >= 1

    def test_cancel_plan(self, client):
        r = client.post("/api/v1/planning/plan", json={"goal": "Cancel test"}, headers=HEADERS)
        plan_id = r.json()["id"]
        response = client.post(f"/api/v1/planning/plan/{plan_id}/cancel", headers=HEADERS)
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"


@pytest.mark.usefixtures("client", "mock_auth")
class TestErrorAnalysisAPI:
    def test_analyze_error(self, client):
        response = client.post(
            "/api/v1/errors/analyze",
            json={
                "error_type": "ValueError",
                "error_message": "test error message",
                "context": {},
            },
            headers=HEADERS,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["error_type"] == "ValueError"
        assert data["fingerprint"] is not None

    def test_get_error_patterns(self, client):
        for i in range(3):
            client.post(
                "/api/v1/errors/analyze",
                json={
                    "error_type": "RuntimeError",
                    "error_message": f"error {i}",
                },
                headers=HEADERS,
            )
        response = client.get("/api/v1/errors/patterns?days=30", headers=HEADERS)
        assert response.status_code == 200

    def test_list_analyses(self, client):
        client.post(
            "/api/v1/errors/analyze",
            json={
                "error_type": "TypeError",
                "error_message": "list test",
            },
            headers=HEADERS,
        )
        response = client.get("/api/v1/errors/analyses", headers=HEADERS)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_resolve_error(self, client):
        r = client.post(
            "/api/v1/errors/analyze",
            json={
                "error_type": "KeyError",
                "error_message": "resolve test",
            },
            headers=HEADERS,
        )
        analysis_id = r.json()["id"]
        response = client.post(f"/api/v1/errors/analysis/{analysis_id}/resolve", headers=HEADERS)
        assert response.status_code == 200
        assert response.json()["resolved"] == 1


@pytest.mark.usefixtures("client", "mock_auth")
class TestHypothesisAPI:
    def test_generate_hypothesis(self, client):
        response = client.post(
            "/api/v1/hypothesis/generate",
            json={
                "hypothesis": "Test hypothesis",
                "source": "test",
            },
            headers=HEADERS,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["hypothesis"] == "Test hypothesis"
        assert data["status"] == "active"
        assert data["confidence"] > 0

    def test_list_active(self, client):
        client.post(
            "/api/v1/hypothesis/generate",
            json={
                "hypothesis": "Active test",
            },
            headers=HEADERS,
        )
        response = client.get("/api/v1/hypothesis/active", headers=HEADERS)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_hypothesis(self, client):
        r = client.post(
            "/api/v1/hypothesis/generate",
            json={
                "hypothesis": "Get test",
            },
            headers=HEADERS,
        )
        hypo_id = r.json()["id"]
        response = client.get(f"/api/v1/hypothesis/{hypo_id}", headers=HEADERS)
        assert response.status_code == 200
        assert response.json()["id"] == hypo_id

    def test_add_evidence(self, client):
        r = client.post(
            "/api/v1/hypothesis/generate",
            json={
                "hypothesis": "Evidence test",
            },
            headers=HEADERS,
        )
        hypo_id = r.json()["id"]
        response = client.post(
            f"/api/v1/hypothesis/{hypo_id}/evidence",
            params={"evidence": "supports this", "supports": True, "weight": 0.9},
            headers=HEADERS,
        )
        assert response.status_code == 200
        assert len(response.json()["evidence_for"]) == 1

    def test_resolve_hypothesis(self, client):
        r = client.post(
            "/api/v1/hypothesis/generate",
            json={
                "hypothesis": "Resolve test",
            },
            headers=HEADERS,
        )
        hypo_id = r.json()["id"]
        response = client.post(
            f"/api/v1/hypothesis/{hypo_id}/resolve",
            params={"status": "confirmed", "reason": "Confirmed by test"},
            headers=HEADERS,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "confirmed"

    def test_high_confidence_filter(self, client):
        client.post(
            "/api/v1/hypothesis/generate",
            json={
                "hypothesis": "Strong hypothesis",
                "evidence_for": [{"text": "e1", "weight": 1.0}, {"text": "e2", "weight": 1.0}],
            },
            headers=HEADERS,
        )
        response = client.get("/api/v1/hypothesis/high-confidence?threshold=0.5", headers=HEADERS)
        assert response.status_code == 200
        assert isinstance(response.json(), list)


@pytest.mark.usefixtures("client", "mock_auth")
class TestConfidenceAPI:
    def test_estimate_confidence(self, client):
        response = client.post(
            "/api/v1/confidence/estimate",
            json={
                "task_type": "planning",
                "context": {},
            },
            headers=HEADERS,
        )
        assert response.status_code == 200
        result = response.json()
        assert 1 <= result["confidence"] <= 99
        assert "recommendation" in result
        assert "risk_level" in result

    def test_combine_confidences(self, client):
        response = client.post(
            "/api/v1/confidence/combine?confidences=70&confidences=80&weights=0.6&weights=0.4",
            headers=HEADERS,
        )
        assert response.status_code == 200
        data = response.json()
        assert "confidence" in data

    def test_get_calibration(self, client):
        response = client.get("/api/v1/confidence/calibration?days=30", headers=HEADERS)
        assert response.status_code == 200
