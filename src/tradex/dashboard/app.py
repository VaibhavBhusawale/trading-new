"""Tradex Streamlit dashboard — talks to the FastAPI backend."""

from __future__ import annotations

import os

import streamlit as st

from tradex import __version__
from tradex.dashboard.api_client import api_base_url, fetch_json, request_json

st.set_page_config(
    page_title="Tradex",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _sidebar() -> None:
    st.sidebar.title("Tradex")
    st.sidebar.caption(f"Dashboard v{__version__}")
    st.sidebar.markdown("---")
    default = os.environ.get("TRADEX_API_URL", "http://127.0.0.1:8000")
    api_url = st.sidebar.text_input("API base URL", value=default)
    os.environ["TRADEX_API_URL"] = api_url.rstrip("/")
    st.sidebar.markdown("**UI:** http://localhost:8501")
    st.sidebar.markdown(f"**API docs:** {api_url.rstrip('/')}/docs")
    if st.sidebar.button("Refresh data", use_container_width=True):
        st.rerun()


def page_overview() -> None:
    st.title("Overview")
    st.warning(
        "Research and paper-trading platform — **not investment advice**. "
        "Live trading is disabled until you complete later phases and enable it explicitly.",
    )

    ok_health, health, err = fetch_json("/api/v1/health")
    ok_cfg, config, err_cfg = fetch_json("/api/v1/config/public")

    if not ok_health:
        st.error(f"Cannot reach API at `{api_base_url()}`. Start the API first.")
        st.code("uvicorn tradex.main:app --host 0.0.0.0 --port 8000", language="bash")
        if err:
            st.caption(err)
        return

    cols = st.columns(4)
    cols[0].metric("API", health.get("status", "?").upper())
    cols[1].metric("Database", health.get("database", "?").upper())
    cols[2].metric("Version", health.get("version", "?"))
    cols[3].metric("Environment", health.get("environment", "?"))

    st.subheader("Active broker")
    b1, b2 = st.columns(2)
    b1.metric(
        "Provider",
        (health.get("active_broker_provider") or health.get("broker_adapter") or "?").upper(),
    )
    b2.metric("Account", health.get("active_broker_name") or "—")
    st.caption("Change broker under the **Brokers** tab (Zerodha, Angel One, Mock, Upstox).")

    st.subheader("Safety gates")
    g1, g2, g3, g4 = st.columns(4)
    g1.metric("Live trading", "ON" if health.get("live_trading_enabled") else "OFF")
    g2.metric("Auto execution", "ON" if health.get("auto_execution_enabled") else "OFF")
    g3.metric("LLM", "ON" if health.get("llm_enabled") else "OFF")
    g4.metric("Kill switch", "ON" if health.get("kill_switch") else "OFF")

    if ok_cfg and config:
        st.subheader("Configuration (no secrets)")
        st.dataframe(
            {
                "Setting": list(config.keys()),
                "Value": [str(v) for v in config.values()],
            },
            use_container_width=True,
            hide_index=True,
        )
        if health.get("database") != "up":
            st.info(
                "Only Postgres belongs in `.env`: set `DATABASE_URL` "
                "(Neon: `postgresql+psycopg://...?sslmode=require`), "
                "then run `alembic upgrade head`. Brokers are configured in the UI."
            )
    elif err_cfg:
        st.caption(f"Config endpoint: {err_cfg}")


def page_brokers() -> None:
    st.title("Broker accounts")
    st.markdown(
        "Add **Zerodha**, **Angel One**, **Upstox**, or **Mock** here. "
        "Secrets are encrypted in Postgres using `API_SECRET_KEY` from `.env`. "
        "Only one account is active at a time."
    )

    ok_p, providers, err_p = fetch_json("/api/v1/brokers/providers")
    ok_a, accounts, err_a = fetch_json("/api/v1/brokers")

    if not ok_p:
        st.error(f"Cannot load providers: {err_p}")
        return
    if not ok_a:
        st.error(
            "Cannot load broker accounts. Ensure `DATABASE_URL` is set and migrations ran."
        )
        st.caption(err_a or "")
        st.code("alembic upgrade head", language="bash")
        return

    st.subheader("Saved accounts")
    if not accounts:
        st.info("No accounts yet — a Mock account is created automatically on first load.")
    else:
        rows = [
            {
                "Active": "✓" if a.get("is_active") else "",
                "Name": a.get("name"),
                "Provider": a.get("provider"),
                "Status": a.get("status"),
                "Has secrets": "yes" if a.get("has_credentials") else "no",
                "Id": str(a.get("id")),
            }
            for a in accounts
        ]
        st.dataframe(rows, use_container_width=True, hide_index=True)

        for account in accounts:
            cols = st.columns([3, 1, 1])
            cols[0].write(
                f"**{account['name']}** · `{account['provider']}` · "
                f"{'ACTIVE' if account['is_active'] else 'inactive'}"
            )
            if not account["is_active"] and cols[1].button(
                "Activate",
                key=f"act_{account['id']}",
            ):
                ok, _, err = request_json(
                    "POST",
                    f"/api/v1/brokers/{account['id']}/activate",
                )
                if ok:
                    st.success(f"Activated {account['name']}")
                    st.rerun()
                else:
                    st.error(err)
            if cols[2].button("Delete", key=f"del_{account['id']}"):
                ok, _, err = request_json("DELETE", f"/api/v1/brokers/{account['id']}")
                if ok:
                    st.success("Deleted")
                    st.rerun()
                else:
                    st.error(err)

    st.markdown("---")
    st.subheader("Add broker account")

    provider_labels = {p["provider"]: p["label"] for p in providers}
    provider_key = st.selectbox(
        "Broker",
        options=[p["provider"] for p in providers],
        format_func=lambda k: provider_labels.get(k, k),
    )
    selected = next(p for p in providers if p["provider"] == provider_key)
    st.caption(selected.get("description", ""))

    name = st.text_input("Account nickname", value=selected["label"])
    notes = st.text_area("Notes (optional)", value="")
    activate = st.checkbox("Make this the active broker", value=True)

    credentials: dict[str, str] = {}
    for field in selected.get("fields", []):
        key = field["key"]
        label = field["label"]
        default = field.get("default") or ""
        if field.get("secret"):
            credentials[key] = st.text_input(
                label,
                type="password",
                key=f"cred_{provider_key}_{key}",
            )
        else:
            credentials[key] = st.text_input(
                label,
                value=default,
                key=f"cred_{provider_key}_{key}",
            )

    if st.button("Save broker account", type="primary"):
        body = {
            "name": name,
            "provider": provider_key,
            "credentials": {k: v for k, v in credentials.items() if v},
            "notes": notes or None,
            "activate": activate,
        }
        ok, data, err = request_json("POST", "/api/v1/brokers", json_body=body)
        if ok:
            st.success(f"Saved `{data.get('name')}` ({data.get('provider')})")
            st.rerun()
        else:
            st.error(err)


def page_system() -> None:
    st.title("System health")
    ok, data, err = fetch_json("/api/v1/health")
    if not ok:
        st.error(f"API unreachable: {err}")
        return
    st.json(data)
    if data.get("database_error"):
        st.error(data["database_error"])


def page_help() -> None:
    st.title("Setup help")
    st.markdown(
        f"""
### URLs
- **Dashboard (this UI):** http://localhost:8501
- **API:** {api_base_url()}
- **Swagger:** {api_base_url()}/docs

### What goes in `.env` only
| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | Neon / Postgres (`postgresql+psycopg://...`) |
| `API_SECRET_KEY` | Encrypts broker secrets stored in the DB |
| `TRADEX_API_URL` | Optional; dashboard API address |

**Broker API keys (Zerodha, Angel One, etc.) are entered in the Brokers tab — not in `.env`.**

### Start locally
```powershell
# Terminal 1 — API
.\\.venv\\Scripts\\Activate.ps1
alembic upgrade head
uvicorn tradex.main:app --host 0.0.0.0 --port 8000

# Terminal 2 — UI
tradex-ui
```
Open **http://127.0.0.1:8501** → **Brokers** tab.
        """
    )


def main() -> None:
    _sidebar()
    overview, brokers, system, help_page = st.tabs(
        ["Overview", "Brokers", "System health", "Setup help"]
    )
    with overview:
        page_overview()
    with brokers:
        page_brokers()
    with system:
        page_system()
    with help_page:
        page_help()


if __name__ == "__main__":
    main()
