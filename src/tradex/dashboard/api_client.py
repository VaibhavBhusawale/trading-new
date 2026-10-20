from __future__ import annotations

import os
from typing import Any

import httpx

DEFAULT_API_URL = "http://127.0.0.1:8000"


def api_base_url() -> str:
    return os.environ.get("TRADEX_API_URL", DEFAULT_API_URL).rstrip("/")


def fetch_json(path: str, timeout: float = 10.0) -> tuple[bool, Any, str | None]:
    return request_json("GET", path, timeout=timeout)


def request_json(
    method: str,
    path: str,
    *,
    json_body: dict[str, Any] | None = None,
    timeout: float = 15.0,
) -> tuple[bool, Any, str | None]:
    url = f"{api_base_url()}{path}"
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.request(method, url, json=json_body)
            if response.status_code == 204:
                return True, None, None
            if response.is_error:
                detail: str
                try:
                    payload = response.json()
                    detail = str(payload.get("detail", payload))
                except Exception:  # noqa: BLE001
                    detail = response.text or str(response.status_code)
                return False, None, detail
            if not response.content:
                return True, None, None
            return True, response.json(), None
    except httpx.HTTPError as exc:
        return False, None, str(exc)
    except Exception as exc:  # noqa: BLE001 — UI surface
        return False, None, str(exc)
