from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from tradex.models.enums import BrokerAccountStatus, BrokerProvider


class BrokerFieldSchema(BaseModel):
    key: str
    label: str
    secret: bool
    required: bool
    default: str | None = None


class BrokerProviderInfo(BaseModel):
    provider: BrokerProvider
    label: str
    description: str
    fields: list[BrokerFieldSchema]
    live_ready: bool


class BrokerAccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    provider: BrokerProvider
    credentials: dict[str, str] = Field(default_factory=dict)
    notes: str | None = None
    activate: bool = False


class BrokerAccountUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    credentials: dict[str, str] | None = None
    notes: str | None = None


class BrokerAccountResponse(BaseModel):
    id: UUID
    name: str
    provider: BrokerProvider
    is_active: bool
    status: BrokerAccountStatus
    public_meta: dict[str, Any]
    notes: str | None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    has_credentials: bool

    model_config = {"from_attributes": True}
