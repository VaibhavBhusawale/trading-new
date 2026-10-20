def test_public_config(client) -> None:
    response = client.get("/api/v1/config/public")
    assert response.status_code == 200
    body = response.json()
    assert body["live_trading_enabled"] is False
    assert body["brokers_via_ui"] is True

