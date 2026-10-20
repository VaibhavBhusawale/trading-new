from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from tradex.brokers.catalog import (
    public_meta_from_credentials,
    validate_credentials,
)
from tradex.models.enums import AuditEventType, BrokerAccountStatus, BrokerProvider
from tradex.models.tables import AuditEvent, BrokerAccount
from tradex.security.secrets import decrypt_credentials, encrypt_credentials


def list_accounts(session: Session) -> list[BrokerAccount]:
    return list(session.scalars(select(BrokerAccount).order_by(BrokerAccount.created_at)).all())


def get_account(session: Session, account_id: uuid.UUID) -> BrokerAccount | None:
    return session.get(BrokerAccount, account_id)


def get_active_account(session: Session) -> BrokerAccount | None:
    return session.scalars(
        select(BrokerAccount).where(BrokerAccount.is_active.is_(True)).limit(1)
    ).first()


def create_account(
    session: Session,
    *,
    name: str,
    provider: BrokerProvider,
    credentials: dict[str, str],
    notes: str | None,
    activate: bool,
) -> BrokerAccount:
    cleaned = {k: (v or "").strip() for k, v in credentials.items() if (v or "").strip()}
    errors = validate_credentials(provider, cleaned)
    if errors:
        raise ValueError("; ".join(errors))

    account = BrokerAccount(
        name=name.strip(),
        provider=provider,
        is_active=False,
        status=BrokerAccountStatus.CONFIGURED
        if provider == BrokerProvider.MOCK or cleaned
        else BrokerAccountStatus.DRAFT,
        credentials_encrypted=encrypt_credentials(cleaned) if cleaned else None,
        public_meta=public_meta_from_credentials(provider, cleaned),
        notes=notes,
    )
    session.add(account)
    session.flush()
    if activate or (provider == BrokerProvider.MOCK and get_active_account(session) is None):
        _set_active(session, account)
    _audit(
        session,
        actor="ui",
        resource_id=str(account.id),
        payload={"action": "create", "provider": provider.value, "name": account.name},
    )
    session.commit()
    session.refresh(account)
    return account


def update_account(
    session: Session,
    account: BrokerAccount,
    *,
    name: str | None,
    credentials: dict[str, str] | None,
    notes: str | None,
) -> BrokerAccount:
    if name is not None:
        account.name = name.strip()
    if notes is not None:
        account.notes = notes

    if credentials is not None:
        existing: dict[str, Any] = {}
        if account.credentials_encrypted:
            existing = decrypt_credentials(account.credentials_encrypted)
        for key, value in credentials.items():
            if value is None:
                continue
            text = value.strip()
            # Empty string means "leave unchanged" for secret fields in UI updates
            if text == "" and key in existing:
                continue
            if text == "":
                existing.pop(key, None)
            else:
                existing[key] = text
        errors = validate_credentials(account.provider, existing)
        if errors:
            raise ValueError("; ".join(errors))
        account.credentials_encrypted = encrypt_credentials(existing) if existing else None
        account.public_meta = public_meta_from_credentials(account.provider, existing)
        account.status = (
            BrokerAccountStatus.CONFIGURED
            if account.provider == BrokerProvider.MOCK or existing
            else BrokerAccountStatus.DRAFT
        )

    _audit(
        session,
        actor="ui",
        resource_id=str(account.id),
        payload={"action": "update", "provider": account.provider.value},
    )
    session.commit()
    session.refresh(account)
    return account


def activate_account(session: Session, account: BrokerAccount) -> BrokerAccount:
    _set_active(session, account)
    _audit(
        session,
        actor="ui",
        resource_id=str(account.id),
        payload={"action": "activate", "provider": account.provider.value},
    )
    session.commit()
    session.refresh(account)
    return account


def delete_account(session: Session, account: BrokerAccount) -> None:
    was_active = account.is_active
    account_id = str(account.id)
    provider = account.provider.value
    session.delete(account)
    session.flush()
    if was_active:
        mock = session.scalars(
            select(BrokerAccount).where(BrokerAccount.provider == BrokerProvider.MOCK).limit(1)
        ).first()
        if mock:
            _set_active(session, mock)
    _audit(
        session,
        actor="ui",
        resource_id=account_id,
        payload={"action": "delete", "provider": provider},
    )
    session.commit()


def ensure_default_mock(session: Session) -> BrokerAccount | None:
    """Create an active mock account when the table is empty."""
    existing = list_accounts(session)
    if existing:
        return get_active_account(session)
    account = BrokerAccount(
        name="Paper / Mock",
        provider=BrokerProvider.MOCK,
        is_active=True,
        status=BrokerAccountStatus.CONFIGURED,
        credentials_encrypted=None,
        public_meta={"configured_fields": []},
        notes="Default safe adapter — no live orders",
    )
    session.add(account)
    _audit(
        session,
        actor="system",
        resource_id="bootstrap",
        payload={"action": "ensure_default_mock"},
    )
    session.commit()
    session.refresh(account)
    return account


def _set_active(session: Session, account: BrokerAccount) -> None:
    session.execute(update(BrokerAccount).values(is_active=False))
    account.is_active = True


def _audit(
    session: Session,
    *,
    actor: str,
    resource_id: str,
    payload: dict[str, Any],
) -> None:
    session.add(
        AuditEvent(
            event_type=AuditEventType.BROKER,
            actor=actor,
            resource_type="broker_account",
            resource_id=resource_id,
            payload=payload,
        )
    )
