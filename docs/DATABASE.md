# Database schema (Phase 2)

Migrations live in `alembic/versions/`. Apply with `alembic upgrade head`.

All timestamps are **UTC** (`timestamptz`). Market session logic uses `MARKET_TIMEZONE` (default `Asia/Kolkata`) in application code.

## Entity relationships (summary)

```text
instruments 1---* candles
strategy_runs 1---* signals *---1 instruments
signals 1---0..1 signal_explanations
signals 0---* paper_orders | live_orders
paper_orders | live_orders 1---* fills
instruments 1---* positions (unique per is_paper)
portfolio_snapshots (EOD marks, paper or live)
risk_events, audit_events (append-only style)
app_settings (key/value JSON)
```

## Idempotency

- `signals.idempotency_key` — unique per generated signal.
- `paper_orders.idempotency_key`, `live_orders.idempotency_key` — unique per order intent.

## Order state machine

`DRAFT` → `PENDING_APPROVAL` → `APPROVED` → `SUBMITTED` → `OPEN` → `PARTIALLY_FILLED` / `FILLED`, with terminal `CANCELLED`, `REJECTED`, `FAILED`.

Live orders add `approved_by` / `approved_at` (Phase 7).

## Retention (planned)

Document per-table retention in the operational runbook (Phase 8). Candles and audit events may grow quickly; use partitioned tables or archival jobs later.

## Secrets

Do **not** store Kite access tokens or API secrets in these tables. Session storage will use a dedicated secure mechanism in Phase 6+.
