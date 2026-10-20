from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = Field(default="tradex", alias="APP_NAME")
    app_env: Literal["development", "test", "staging", "production"] = Field(
        default="development",
        alias="APP_ENV",
    )
    app_debug: bool = Field(default=False, alias="APP_DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(
        default=8000,
        validation_alias=AliasChoices("API_PORT", "PORT"),
    )
    public_base_url: str = Field(
        default="",
        alias="PUBLIC_BASE_URL",
        description="Public URL of this deployment (e.g. https://tradex-api.onrender.com)",
    )
    cors_origins: str = Field(default="", alias="CORS_ORIGINS")
    market_timezone: str = Field(default="Asia/Kolkata", alias="MARKET_TIMEZONE")

    database_url: str = Field(
        default="postgresql+psycopg://tradex:tradex@localhost:5432/tradex",
        alias="DATABASE_URL",
    )
    database_pool_size: int = Field(default=5, alias="DATABASE_POOL_SIZE")
    database_echo: bool = Field(default=False, alias="DATABASE_ECHO")

    llm_enabled: bool = Field(default=False, alias="LLM_ENABLED")
    live_trading_enabled: bool = Field(default=False, alias="LIVE_TRADING_ENABLED")
    auto_execution_enabled: bool = Field(default=False, alias="AUTO_EXECUTION_ENABLED")
    paper_trading_enabled: bool = Field(default=True, alias="PAPER_TRADING_ENABLED")

    llm_provider: str = Field(default="openai", alias="LLM_PROVIDER")
    llm_model: str = Field(default="gpt-4o-mini", alias="LLM_MODEL")
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_max_tokens: int = Field(default=2048, alias="LLM_MAX_TOKENS")
    llm_timeout_seconds: int = Field(default=60, alias="LLM_TIMEOUT_SECONDS")
    llm_max_retries: int = Field(default=2, alias="LLM_MAX_RETRIES")

    kite_api_key: str = Field(default="", alias="KITE_API_KEY")
    kite_api_secret: str = Field(default="", alias="KITE_API_SECRET")
    kite_redirect_url: str = Field(
        default="http://127.0.0.1:8000/api/v1/broker/kite/callback",
        alias="KITE_REDIRECT_URL",
    )
    # Fallback only when no active broker_account in DB (UI is the source of truth)
    broker_adapter: Literal["mock", "kite", "zerodha", "angel_one", "upstox"] = Field(
        default="mock",
        alias="BROKER_ADAPTER",
    )

    max_risk_per_trade_pct: float = Field(default=1.0, alias="MAX_RISK_PER_TRADE_PCT")
    max_position_size_pct: float = Field(default=10.0, alias="MAX_POSITION_SIZE_PCT")
    max_daily_loss_pct: float = Field(default=3.0, alias="MAX_DAILY_LOSS_PCT")
    max_portfolio_exposure_pct: float = Field(default=80.0, alias="MAX_PORTFOLIO_EXPOSURE_PCT")
    kill_switch: bool = Field(default=False, alias="KILL_SWITCH")
    stale_data_max_age_minutes: int = Field(default=30, alias="STALE_DATA_MAX_AGE_MINUTES")

    auth_enabled: bool = Field(default=False, alias="AUTH_ENABLED")
    api_secret_key: str = Field(default="change-me", alias="API_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    @field_validator("app_debug", mode="before")
    @classmethod
    def parse_bool(cls, value: object) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(value)

    def cors_origin_list(self) -> list[str]:
        if not self.cors_origins.strip():
            return []
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
