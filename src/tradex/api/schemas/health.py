from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(description="ok | degraded")
    app_name: str
    version: str
    environment: str
    database: str = Field(description="up | down | skipped")
    database_error: str | None = None
    broker_adapter: str
    active_broker_provider: str | None = None
    active_broker_name: str | None = None
    live_trading_enabled: bool
    auto_execution_enabled: bool
    llm_enabled: bool
    kill_switch: bool
