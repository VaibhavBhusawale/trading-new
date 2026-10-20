from tradex.brokers.catalog import validate_credentials
from tradex.models.enums import BrokerProvider
from tradex.security.secrets import decrypt_credentials, encrypt_credentials, mask_secret


def test_zerodha_requires_keys() -> None:
    errors = validate_credentials(BrokerProvider.ZERODHA, {})
    assert any("API Key" in e for e in errors)


def test_angel_requires_client_code() -> None:
    errors = validate_credentials(
        BrokerProvider.ANGEL_ONE,
        {"api_key": "x"},
    )
    assert any("Client Code" in e for e in errors)


def test_mock_needs_no_credentials() -> None:
    assert validate_credentials(BrokerProvider.MOCK, {}) == []


def test_encrypt_roundtrip(monkeypatch) -> None:
    monkeypatch.setenv("API_SECRET_KEY", "unit-test-secret-key-12345")
    from tradex.config.settings import get_settings

    get_settings.cache_clear()
    token = encrypt_credentials({"api_key": "abc", "api_secret": "xyz"})
    assert "abc" not in token
    assert decrypt_credentials(token) == {"api_key": "abc", "api_secret": "xyz"}
    get_settings.cache_clear()


def test_mask_secret() -> None:
    assert mask_secret("abcdefgh") == "****efgh"
