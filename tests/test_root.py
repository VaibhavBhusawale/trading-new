def test_root(client) -> None:
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "tradex"
    assert body["health_path"] == "/health"
    assert body["docs_path"] == "/docs"
