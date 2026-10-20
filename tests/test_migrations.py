import os

import pytest
from sqlalchemy import inspect

from tradex.config.settings import get_settings
from tradex.db.session import check_database_connection, get_engine, reset_engine_cache


@pytest.fixture
def db_engine():
    os.environ.setdefault("APP_ENV", "test")
    get_settings.cache_clear()
    reset_engine_cache()
    engine = get_engine()
    yield engine
    engine.dispose()
    get_settings.cache_clear()
    reset_engine_cache()


@pytest.mark.integration
def test_schema_tables_exist(db_engine) -> None:
    ok, _ = check_database_connection()
    if not ok:
        pytest.skip("PostgreSQL not reachable; start docker compose or set DATABASE_URL")

    from alembic import command
    from alembic.config import Config

    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

    inspector = inspect(db_engine)
    tables = set(inspector.get_table_names())
    expected = {
        "instruments",
        "candles",
        "strategy_runs",
        "signals",
        "signal_explanations",
        "paper_orders",
        "live_orders",
        "fills",
        "positions",
        "portfolio_snapshots",
        "risk_events",
        "audit_events",
        "app_settings",
        "broker_accounts",
        "alembic_version",
    }
    missing = expected - tables
    assert not missing, f"Missing tables: {missing}"
