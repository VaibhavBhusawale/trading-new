from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from tradex.api.schemas.brokers import (
    BrokerAccountCreate,
    BrokerAccountResponse,
    BrokerAccountUpdate,
    BrokerProviderInfo,
)
from tradex.brokers.catalog import PROVIDER_CATALOG
from tradex.db.session import check_database_connection, get_db
from tradex.models.tables import BrokerAccount
from tradex.services import broker_accounts as svc

router = APIRouter(prefix="/brokers", tags=["brokers"])
DbSession = Annotated[Session, Depends(get_db)]


def _to_response(account: BrokerAccount) -> BrokerAccountResponse:
    return BrokerAccountResponse(
        id=account.id,
        name=account.name,
        provider=account.provider,
        is_active=account.is_active,
        status=account.status,
        public_meta=account.public_meta or {},
        notes=account.notes,
        created_at=account.created_at,
        updated_at=account.updated_at,
        has_credentials=bool(account.credentials_encrypted),
    )


def _require_db() -> None:
    ok, err = check_database_connection()
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database unavailable. Set DATABASE_URL in .env. ({err})",
        )


def _not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Broker account not found",
    )


@router.get("/providers", response_model=list[BrokerProviderInfo])
def list_providers() -> list[BrokerProviderInfo]:
    return [BrokerProviderInfo.model_validate(item) for item in PROVIDER_CATALOG]


@router.get("", response_model=list[BrokerAccountResponse])
def list_broker_accounts(db: DbSession) -> list[BrokerAccountResponse]:
    _require_db()
    svc.ensure_default_mock(db)
    return [_to_response(a) for a in svc.list_accounts(db)]


@router.get("/active", response_model=BrokerAccountResponse | None)
def get_active_broker(db: DbSession) -> BrokerAccountResponse | None:
    _require_db()
    svc.ensure_default_mock(db)
    active = svc.get_active_account(db)
    return _to_response(active) if active else None


@router.post("", response_model=BrokerAccountResponse, status_code=status.HTTP_201_CREATED)
def create_broker_account(
    body: BrokerAccountCreate,
    db: DbSession,
) -> BrokerAccountResponse:
    _require_db()
    try:
        account = svc.create_account(
            db,
            name=body.name,
            provider=body.provider,
            credentials=body.credentials,
            notes=body.notes,
            activate=body.activate,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _to_response(account)


@router.patch("/{account_id}", response_model=BrokerAccountResponse)
def update_broker_account(
    account_id: UUID,
    body: BrokerAccountUpdate,
    db: DbSession,
) -> BrokerAccountResponse:
    _require_db()
    account = svc.get_account(db, account_id)
    if not account:
        raise _not_found()
    try:
        account = svc.update_account(
            db,
            account,
            name=body.name,
            credentials=body.credentials,
            notes=body.notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _to_response(account)


@router.post("/{account_id}/activate", response_model=BrokerAccountResponse)
def activate_broker_account(account_id: UUID, db: DbSession) -> BrokerAccountResponse:
    _require_db()
    account = svc.get_account(db, account_id)
    if not account:
        raise _not_found()
    return _to_response(svc.activate_account(db, account))


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_broker_account(account_id: UUID, db: DbSession) -> None:
    _require_db()
    account = svc.get_account(db, account_id)
    if not account:
        raise _not_found()
    svc.delete_account(db, account)
