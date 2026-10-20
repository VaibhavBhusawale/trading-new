"""Supported brokers and credential fields shown in the UI."""

from __future__ import annotations

from typing import Any

from tradex.models.enums import BrokerProvider

PROVIDER_CATALOG: list[dict[str, Any]] = [
    {
        "provider": BrokerProvider.MOCK.value,
        "label": "Paper / Mock (no broker account)",
        "description": "Simulated broker for development and paper trading. No API keys.",
        "fields": [],
        "live_ready": False,
    },
    {
        "provider": BrokerProvider.ZERODHA.value,
        "label": "Zerodha Kite Connect",
        "description": "Official Kite Connect API. Login session is separate (OAuth).",
        "fields": [
            {
                "key": "api_key",
                "label": "API Key",
                "secret": True,
                "required": True,
            },
            {
                "key": "api_secret",
                "label": "API Secret",
                "secret": True,
                "required": True,
            },
            {
                "key": "redirect_url",
                "label": "Redirect URL",
                "secret": False,
                "required": False,
                "default": "http://127.0.0.1:8000/api/v1/broker/kite/callback",
            },
        ],
        "live_ready": False,
    },
    {
        "provider": BrokerProvider.ANGEL_ONE.value,
        "label": "Angel One SmartAPI",
        "description": (
            "Angel One SmartAPI. Prefer API key + client code; "
            "avoid storing TOTP long-term."
        ),
        "fields": [
            {
                "key": "api_key",
                "label": "API Key",
                "secret": True,
                "required": True,
            },
            {
                "key": "client_code",
                "label": "Client Code",
                "secret": False,
                "required": True,
            },
            {
                "key": "password",
                "label": "PIN / Password",
                "secret": True,
                "required": False,
            },
            {
                "key": "totp_secret",
                "label": "TOTP Secret (optional)",
                "secret": True,
                "required": False,
            },
        ],
        "live_ready": False,
    },
    {
        "provider": BrokerProvider.UPSTOX.value,
        "label": "Upstox (planned)",
        "description": "Placeholder — configure credentials now; adapter comes later.",
        "fields": [
            {
                "key": "api_key",
                "label": "API Key",
                "secret": True,
                "required": True,
            },
            {
                "key": "api_secret",
                "label": "API Secret",
                "secret": True,
                "required": True,
            },
            {
                "key": "redirect_url",
                "label": "Redirect URL",
                "secret": False,
                "required": False,
            },
        ],
        "live_ready": False,
    },
]


def catalog_for(provider: BrokerProvider | str) -> dict[str, Any]:
    key = provider.value if isinstance(provider, BrokerProvider) else provider
    for item in PROVIDER_CATALOG:
        if item["provider"] == key:
            return item
    raise KeyError(f"Unknown broker provider: {key}")


def validate_credentials(provider: BrokerProvider, credentials: dict[str, str]) -> list[str]:
    catalog = catalog_for(provider)
    errors: list[str] = []
    for field in catalog["fields"]:
        if field["required"] and not (credentials.get(field["key"]) or "").strip():
            errors.append(f"{field['label']} is required")
    return errors


def public_meta_from_credentials(
    provider: BrokerProvider,
    credentials: dict[str, str],
) -> dict[str, Any]:
    from tradex.security.secrets import mask_secret

    catalog = catalog_for(provider)
    meta: dict[str, Any] = {"configured_fields": []}
    for field in catalog["fields"]:
        key = field["key"]
        value = (credentials.get(key) or "").strip()
        if not value:
            continue
        meta["configured_fields"].append(key)
        if field["secret"]:
            meta[f"{key}_masked"] = mask_secret(value)
        else:
            meta[key] = value
    return meta
