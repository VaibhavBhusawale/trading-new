from fastapi import APIRouter

from tradex import __version__
from tradex.api.schemas.root import RootResponse
from tradex.config import get_settings

router = APIRouter(tags=["meta"])


@router.get("/", response_model=RootResponse)
def read_root() -> RootResponse:
    settings = get_settings()
    base = settings.public_base_url.rstrip("/") if settings.public_base_url else None
    return RootResponse(
        service=settings.app_name,
        version=__version__,
        health_url=f"{base}/health" if base else None,
        docs_url=f"{base}/docs" if base else None,
    )
