import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from tradex import __version__
from tradex.api.routes import brokers_router, config_router, health_router, root_router
from tradex.config import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)
    logger.info(
        "Starting %s v%s env=%s broker=%s live=%s auto=%s",
        settings.app_name,
        __version__,
        settings.app_env,
        settings.broker_adapter,
        settings.live_trading_enabled,
        settings.auto_execution_enabled,
    )
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Tradex API",
        version=__version__,
        description="NSE equity research and gated trading (not investment advice).",
        lifespan=lifespan,
    )
    origins = settings.cors_origin_list()
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
            allow_headers=["*"],
        )

    app.include_router(root_router)
    app.include_router(health_router)
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(config_router, prefix="/api/v1")
    app.include_router(brokers_router, prefix="/api/v1")

    return app


app = create_app()


def run() -> None:
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "tradex.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.app_env == "development",
    )


if __name__ == "__main__":
    run()
