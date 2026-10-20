from pydantic import BaseModel, Field


class RootResponse(BaseModel):
    service: str
    version: str
    message: str = Field(
        default="API is running. Trading/scanner features arrive in later phases.",
        description="Short status for browsers and uptime checks.",
    )
    health_path: str = "/health"
    docs_path: str = "/docs"
    health_url: str | None = None
    docs_url: str | None = None
