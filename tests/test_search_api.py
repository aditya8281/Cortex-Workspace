from unittest.mock import AsyncMock, MagicMock, patch

HEADERS = {"Authorization": "Bearer fake-token"}


def _make_retrieval_result(content="test content", source="vector", score=0.9, file_path="test.py", document_id=1, language="python", chunk_type="code"):
    r = MagicMock()
    r.content = content
    r.source = source
    r.score = score
    r.file_path = file_path
    r.document_id = document_id
    r.language = language
    r.chunk_type = chunk_type
    return r


def test_search_get(client, mock_auth):
    result = _make_retrieval_result()
    with patch("backend.app.api.v1.search.HybridRetrievalV2") as mock_retrieval:
        mock_retrieval.return_value.retrieve.return_value = [result]
        resp = client.get("/api/v1/search?query=test+query", headers=HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["query"] == "test query"
        assert len(data["results"]) == 1
        assert data["results"][0]["content"] == "test content"
        assert data["results"][0]["source"] == "vector"


def test_search_post(client, mock_auth):
    result = _make_retrieval_result()
    with patch("backend.app.api.v1.search.HybridRetrievalV2") as mock_retrieval:
        mock_retrieval.return_value.retrieve.return_value = [result]
        resp = client.post(
            "/api/v1/search",
            json={"query": "test query", "max_results": 5},
            headers=HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["query"] == "test query"


def test_search_answer(client, mock_auth):
    result = _make_retrieval_result(content="relevant code snippet")

    with (
        patch("backend.app.api.v1.search.HybridRetrievalV2") as mock_retrieval,
        patch("backend.app.services.llm.manager.llm_manager") as mock_llm,
    ):
        mock_retrieval.return_value.retrieve.return_value = [result]
        mock_llm.chat = AsyncMock(return_value=MagicMock(content="This is the AI answer."))

        resp = client.post(
            "/api/v1/search/answer",
            json={"query": "what does this code do?", "max_results": 5},
            headers=HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["answer"] == "This is the AI answer."
        assert data["query"] == "what does this code do?"
        assert len(data["results"]) == 1


def test_search_empty_query(client, mock_auth):
    with patch("backend.app.api.v1.search.HybridRetrievalV2") as mock_retrieval:
        mock_retrieval.return_value.retrieve.return_value = []
        resp = client.post(
            "/api/v1/search",
            json={"query": "x", "max_results": 10},
            headers=HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["results"] == []
