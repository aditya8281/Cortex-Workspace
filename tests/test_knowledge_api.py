def test_knowledge_health(client, mock_auth):
    resp = client.get("/api/v1/knowledge/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert isinstance(data["documents_indexed"], int)
    assert isinstance(data["total_chunks"], int)
    assert isinstance(data["graph_nodes"], int)
    assert isinstance(data["graph_edges"], int)
    assert isinstance(data["repos_indexed"], int)
    assert isinstance(data["code_chunks"], int)


def test_knowledge_stats(client, mock_auth):
    resp = client.get("/api/v1/knowledge/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data["documents_by_type"], dict)
    assert isinstance(data["chunks_by_language"], dict)
    assert isinstance(data["avg_chunks_per_document"], float)
    assert isinstance(data["graph_edge_types"], dict)
