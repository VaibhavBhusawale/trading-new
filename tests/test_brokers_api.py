def test_list_providers(client) -> None:
    response = client.get("/api/v1/brokers/providers")
    assert response.status_code == 200
    providers = {p["provider"] for p in response.json()}
    assert {"mock", "zerodha", "angel_one", "upstox"} <= providers


def test_brokers_list_without_db_returns_503(client) -> None:
    # conftest points DATABASE_URL at unreachable port
    response = client.get("/api/v1/brokers")
    assert response.status_code == 503


def test_config_marks_brokers_via_ui(client) -> None:
    response = client.get("/api/v1/config/public")
    assert response.status_code == 200
    assert response.json()["brokers_via_ui"] is True
