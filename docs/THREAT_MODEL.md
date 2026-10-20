# Tradex — Threat Model (Phase 1)

## Scope

Tradex running locally or on a single VPS with FastAPI, PostgreSQL, optional Streamlit, optional Zerodha Kite Connect, and optional LLM/notifications.

## Assets

| Asset | Sensitivity |
|-------|-------------|
| `KITE_API_SECRET`, `API_SECRET_KEY`, DB credentials | Critical |
| Kite access token (session) | Critical |
| `LLM_API_KEY` | High |
| Portfolio, orders, PII in DB | High |
| Strategy parameters, audit logs | Medium |
| Market candles (licensed) | Medium |

## Trust boundaries

```text
[User browser] --TLS--> [API / Streamlit]
                            |
              +-------------+-------------+
              |             |             |
         [PostgreSQL]   [Kite API]    [LLM API]
         (private net)  (internet)   (internet)
```

- **Untrusted**: HTTP request bodies, query params, LLM outputs, news text, webhook payloads.
- **Semi-trusted**: Scheduled jobs (must use same gates as API).
- **Trusted**: Risk manager code, migration SQL, operator with DB access.

## Threats and mitigations

### T1 — Credential theft from repo or logs

- **Risk**: Committed `.env`, logged headers, exception traces with URLs containing tokens.
- **Mitigation**: `.gitignore` for `.env`; structured logging with redaction; never log `Authorization` or Kite tokens; `.env.example` placeholders only.

### T2 — Unauthorized API access

- **Risk**: Public deployment without auth; order endpoints abused.
- **Mitigation**: `AUTH_ENABLED` default false for local dev; document mandatory auth + TLS before production; rate limits on sensitive routes (Phase 7+); live trading behind explicit flag.

### T3 — Prompt injection via news / explanations

- **Risk**: Malicious text in news causes model to emit “BUY” or tool calls.
- **Mitigation**: LLM has no direct order tools; trade proposals only via Pydantic-validated deterministic pipeline; execution requires separate human confirmation and risk checks.

### T4 — Duplicate or replay orders

- **Risk**: Double-submit on retry or crash.
- **Mitigation**: Idempotency keys on orders; unique constraints; reconcile state before new live orders.

### T5 — Stale or manipulated market data

- **Risk**: Trades on old candles or corrupted feed.
- **Mitigation**: Freshness checks; `STALE_DATA_MAX_AGE_MINUTES`; block execution when data invalid; source attribution on candles.

### T6 — SQL injection / unsafe deserialization

- **Risk**: Raw SQL from user input.
- **Mitigation**: SQLAlchemy ORM; parameterized queries; Pydantic input validation on APIs.

### T7 — Kill switch bypass

- **Risk**: Background job submits while operator halted trading.
- **Mitigation**: Central execution gate reading `KILL_SWITCH` and `AUTO_EXECUTION_ENABLED`; audit log on state changes.

### T8 — Over-exposure / runaway losses

- **Risk**: Bug sizes positions too large.
- **Mitigation**: Deterministic risk manager caps; daily loss limit; max exposure; paper mode default.

### T9 — Session hijacking (Kite)

- **Risk**: Stolen access token places orders.
- **Mitigation**: Short-lived tokens; store outside LLM context; HTTP-only secure cookies when web login added; rotate on logout; least-privilege API key.

### T10 — Dependency supply chain

- **Risk**: Compromised PyPI package.
- **Mitigation**: Pinned versions in `pyproject.toml`; GitHub Actions CI; document `pip-audit` / Dependabot guidance.

## STRIDE summary

| Category | Example | Control |
|----------|---------|---------|
| Spoofing | Fake user confirms order | Auth + signed confirm token (Phase 7) |
| Tampering | DB order state changed | Audit events; broker reconciliation |
| Repudiation | “I didn’t approve” | Append-only audit with actor + timestamp |
| Information disclosure | DB exposed to internet | Private network; no public Postgres |
| Denial of service | Scan endpoint flood | Rate limits; job backoff |
| Elevation | CI runs live trades | `BROKER_ADAPTER=mock` in CI; no secrets in Actions |

## Failure modes (operational)

| Failure | Expected behavior |
|---------|-------------------|
| Kite session expired | Read/write orders fail with clear error; no silent retry with stored password |
| Partial fill | Order state `PARTIALLY_FILLED`; reconcile before new orders |
| Gap through stop | Document no guarantee; P&L computed from actual fills |
| DB down | Health check `degraded`; no execution |
| LLM timeout | Fallback to rule-only explanations; app continues |

## Compliance notes (non-legal)

Operators must verify SEBI, exchange, and broker terms before live trading. This software is a tool; **no automated compliance certification** is implied. Keep audit logs per retention policy.

## Open items (later phases)

- Encrypt Kite access token at rest (KMS or app-level key).
- mTLS between services if split into multiple hosts.
- Formal RBAC for multi-user teams.
- Penetration test before production.
