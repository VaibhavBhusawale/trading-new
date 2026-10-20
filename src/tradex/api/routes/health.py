from fastapi import APIRouter

from tradex import __version__
from tradex.api.schemas.health import HealthResponse
from tradex.config import get_settings
from tradex.db.session import check_database_connection, get_session_factory
from tradex.services import broker_accounts as broker_svc

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    settings = get_settings()
    db_ok, db_err = check_database_connection()
    status = "ok" if db_ok else "degraded"

    active_provider: str | None = None
    active_name: str | None = None
    broker_adapter = settings.broker_adapter
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
        except Exception:  # noqa: BLE001 — health must not fail
            pass

    return HealthResponse(
        status=status,
        app_name=settings.app_name,
        version=__version__,
        environment=settings.app_env,
        database="up" if db_ok else "down",
        database_error=db_err,
        broker_adapter=broker_adapter,
        active_broker_provider=active_provider,
        active_broker_name=active_name,
        live_trading_enabled=settings.live_trading_enabled,
        auto_execution_enabled=settings.auto_execution_enabled,
        llm_enabled=settings.llm_enabled,
        kill_switch=settings.kill_switch,
    )
