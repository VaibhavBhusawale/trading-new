# Tradex

Production-minded, AI-assisted **NSE cash-equity** research platform with Zerodha Kite Connect integration (phased). Default mode is **recommendations and paper trading**; live and automated execution are **disabled by default**.

**This software does not guarantee profits.** Backtest and paper-trade strategies before any real capital.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Threat model](docs/THREAT_MODEL.md)
- [Deployment (public URL)](docs/DEPLOYMENT.md)

## Requirements

- Python **3.12** (developed on 3.12.10)
- PostgreSQL 15+ ([Neon](https://neon.tech) free tier or local via Docker Compose)
- Optional: Docker Desktop for local PostgreSQL

## Quick start (Phase 2)

### 1. Clone and install

```powershell
cd "path\to\Trading"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

### 2. Configure environment

```powershell
Copy-Item .env.example .env
# Edit DATABASE_URL for Neon or local Postgres
```

Default local URL (matches `docker-compose.yml`):

`postgresql+psycopg://tradex:tradex@localhost:5432/tradex`

### 3. Start PostgreSQL (optional)

If Docker is installed:

```powershell
docker compose up -d postgres
```

### 4. Run migrations

```powershell
alembic upgrade head
```

### 5. Run API

```powershell
uvicorn tradex.main:app --reload --host 0.0.0.0 --port 8000
```

URLs:

- `http://127.0.0.1:8000/` — service info
- `http://127.0.0.1:8000/health` and `/api/v1/health`
- `http://127.0.0.1:8000/docs` — OpenAPI UI

### Dashboard UI (Streamlit)

Install UI dependencies once:

```powershell
pip install -e ".[dashboard]"
```

**`.env` only needs Postgres + encryption key** (`DATABASE_URL`, `API_SECRET_KEY`).  
Add **Zerodha / Angel One / Upstox / Mock** under the **Brokers** tab in the UI.

**Terminal 1 — API** (must be running first):

```powershell
alembic upgrade head
uvicorn tradex.main:app --host 0.0.0.0 --port 8000
```

**Terminal 2 — UI:**

```powershell
tradex-ui
```

Open **http://127.0.0.1:8501** → **Brokers** to pick the account.

### Public URL (Docker or cloud)

```powershell
docker compose up -d --build
```

- API: **http://localhost:8000**
- **UI: http://localhost:8501**

For HTTPS on the internet, see **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** (Render + Neon or similar).

### 6. Tests

```powershell
pytest
ruff check src tests
mypy src/tradex
```

Integration tests that need PostgreSQL are skipped automatically if the database is unreachable.

## Zerodha Kite Connect (later phases)

- Register an app in the [Kite Connect developer console](https://kite.trade/docs/connect/v3/).
- Set `KITE_API_KEY`, `KITE_API_SECRET`, and `KITE_REDIRECT_URL` in `.env` only.
- Use `BROKER_ADAPTER=mock` for development and CI.
- Access tokens expire; users must complete the documented OAuth login again—**passwords and TOTP are never stored by this app**.

Verify current API fees, static IP requirements, and regulatory obligations before live orders.

## Feature flags (safe defaults)

| Variable | Default | Meaning |
|----------|---------|---------|
| `LLM_ENABLED` | `false` | No external LLM calls |
| `LIVE_TRADING_ENABLED` | `false` | Live order APIs rejected |
| `AUTO_EXECUTION_ENABLED` | `false` | No unattended execution |
| `BROKER_ADAPTER` | `mock` | Simulated broker |
| `KILL_SWITCH` | `false` | When `true`, blocks execution paths |

## Project status

| Phase | Status |
|-------|--------|
| 1 Architecture & threat model | Done |
| 2 Scaffold, DB, health, CI | Done |
| 3 Scanner & signals | Planned |
| 4 Backtest & paper | Planned |
| 5 Dashboard & scheduler | Planned |
| 6 Kite read-only | Planned |
| 7 Human-approved live orders | Planned |

## License

Proprietary — for your personal repository.
