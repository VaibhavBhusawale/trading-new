import os

import pytest
from fastapi.testclient import TestClient

from tradex.config.settings import get_settings
from tradex.db.session import reset_engine_cache
from tradex.main import create_app


@pytest.fixture
def client() -> TestClient:
    os.environ.setdefault("APP_ENV", "test")
    os.environ.setdefault("BROKER_ADAPTER", "mock")
    # Unreachable port so health checks fail fast without a local Postgres
    os.environ.setdefault(
        "DATABASE_URL",
        "postgresql+psycopg://tradex:tradex@127.0.0.1:1/tradex",
    )
    get_settings.cache_clear()
    reset_engine_cache()
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
    get_settings.cache_clear()
    reset_engine_cache()
