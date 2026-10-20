# Deployment — public URL

Tradex is an **API** (FastAPI). After deploy you get URLs like:

| Path | Purpose |
|------|---------|
| `/` | Service info and links |
| `/health` | Liveness + DB status |
| `/docs` | Swagger UI |

**This is not a trading terminal yet** — only health/metadata until Phases 3–7.

## Option A — Docker Compose (local URL)

Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/).

```powershell
docker compose up -d --build
```

Open **http://localhost:8000** (and `/docs`, `/health`).

Stop: `docker compose down`

## Option B — Render + Neon (free-tier friendly public HTTPS URL)

1. Push this repo to **GitHub** (no `.env` in git).
2. Create a [Neon](https://neon.tech) PostgreSQL database.
3. Copy the connection string and change the scheme to **`postgresql+psycopg://`** (not `postgresql://` alone).
   - Example: `postgresql+psycopg://user:pass@ep-xxx.region.aws.neon.tech/neondb?sslmode=require`
4. On [Render](https://render.com): **New → Blueprint** (or **Web Service → Docker**), connect the repo.
5. Set environment variables:
   - `DATABASE_URL` — Neon URL (required)
   - `PUBLIC_BASE_URL` — your Render URL, e.g. `https://tradex-api.onrender.com`
   - `APP_ENV=production`
   - Keep `LIVE_TRADING_ENABLED=false`, `BROKER_ADAPTER=mock` until later phases
6. Deploy. Render sets `PORT` automatically; the Docker entrypoint uses it.

Health check path: `/health`

**Free tier:** service may sleep when idle; first request can be slow.

## Option C — Run on your PC, temporary public URL (dev only)

Tools like [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) or ngrok can expose `localhost:8000`. Use only for testing; enable `AUTH_ENABLED` before sharing widely.

```powershell
uvicorn tradex.main:app --host 0.0.0.0 --port 8000
```

## Security before sharing a URL

- Do **not** expose PostgreSQL to the internet.
- Set a strong `API_SECRET_KEY`; plan to enable `AUTH_ENABLED` before public use.
- Keep `LIVE_TRADING_ENABLED=false` until Phase 7 and you understand broker/compliance requirements.

## Git push checklist

```powershell
git init
git add .
git commit -m "Initial Tradex scaffold"
git remote add origin https://github.com/YOU/tradex.git
git push -u origin main
```

Never commit `.env` or API secrets.
