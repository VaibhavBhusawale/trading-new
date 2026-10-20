def test_root_health(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["app_name"] == "tradex"
    assert body["version"] == "0.1.0"
    assert body["live_trading_enabled"] is False
    assert body["auto_execution_enabled"] is False
    assert body["broker_adapter"] == "mock"
    assert body["status"] in {"ok", "degraded"}
    assert body["database"] in {"up", "down"}


def test_v1_health(client) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] in {"ok", "degraded"}
