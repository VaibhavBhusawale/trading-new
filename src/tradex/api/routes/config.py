from fastapi import APIRouter

from tradex.api.schemas.config import PublicConfigResponse
from tradex.config import get_settings
from tradex.db.session import check_database_connection, get_session_factory
from tradex.services import broker_accounts as broker_svc

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/public", response_model=PublicConfigResponse)
def public_config() -> PublicConfigResponse:
    settings = get_settings()
    broker_adapter = settings.broker_adapter
    active_provider: str | None = None
    active_name: str | None = None
    db_ok, _ = check_database_connection()
    if db_ok:
        try:
            session = get_session_factory()()
            try:
                active = broker_svc.get_active_account(session)
                if active:
                    active_provider = active.provider.value
                    active_name = active.name
                    broker_adapter = active.provider.value
            finally:
                session.close()
        except Exception:  # noqa: BLE001
            pass

    return PublicConfigResponse(
        app_name=settings.app_name,
        environment=settings.app_env,
        broker_adapter=broker_adapter,
        active_broker_provider=active_provider,
        active_broker_name=active_name,
        brokers_via_ui=True,
        database_url_configured=bool(settings.database_url.strip()),
        llm_enabled=settings.llm_enabled,
        live_trading_enabled=settings.live_trading_enabled,
        auto_execution_enabled=settings.auto_execution_enabled,
        paper_trading_enabled=settings.paper_trading_enabled,
        kill_switch=settings.kill_switch,
        market_timezone=settings.market_timezone,
    )
