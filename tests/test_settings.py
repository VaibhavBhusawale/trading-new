import os

from tradex.config.settings import Settings, get_settings
from tradex.db.session import reset_engine_cache


def test_safe_defaults() -> None:
    os.environ["LLM_ENABLED"] = "false"
    os.environ["LIVE_TRADING_ENABLED"] = "false"
    os.environ["AUTO_EXECUTION_ENABLED"] = "false"
    os.environ["BROKER_ADAPTER"] = "mock"
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.llm_enabled is False
    assert settings.live_trading_enabled is False
    assert settings.auto_execution_enabled is False
    assert settings.broker_adapter == "mock"
    get_settings.cache_clear()
    reset_engine_cache()


def test_cors_parsing() -> None:
    settings = Settings(CORS_ORIGINS="http://a.com, http://b.com")
    assert settings.cors_origin_list() == ["http://a.com", "http://b.com"]
