from pydantic import BaseModel, Field


class PublicConfigResponse(BaseModel):
    """Non-secret configuration for the dashboard."""

    app_name: str
    environment: str
    broker_adapter: str
    active_broker_provider: str | None = None
    active_broker_name: str | None = None
    brokers_via_ui: bool = Field(
        default=True,
        description="Broker accounts are managed from the UI, not .env",
    )
    database_url_configured: bool
    llm_enabled: bool
    live_trading_enabled: bool
    auto_execution_enabled: bool
    paper_trading_enabled: bool
    kill_switch: bool
    market_timezone: str
