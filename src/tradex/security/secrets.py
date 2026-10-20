"""Encrypt/decrypt broker credentials at rest using API_SECRET_KEY."""

from __future__ import annotations

import base64
import hashlib
import json
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from tradex.config import get_settings


def _fernet() -> Fernet:
    settings = get_settings()
    digest = hashlib.sha256(settings.api_secret_key.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_credentials(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return _fernet().encrypt(raw).decode("utf-8")


def decrypt_credentials(token: str) -> dict[str, Any]:
    try:
        raw = _fernet().decrypt(token.encode("utf-8"))
    except InvalidToken as exc:
        raise ValueError("Unable to decrypt credentials; check API_SECRET_KEY") from exc
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Invalid credentials payload")
    return data


def mask_secret(value: str | None, visible: int = 4) -> str | None:
    if not value:
        return None
    if len(value) <= visible:
        return "*" * len(value)
    return f"{'*' * (len(value) - visible)}{value[-visible:]}"
