"""initial_schema

Revision ID: 20260320_0001
Revises:
Create Date: 2026-03-20

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260320_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

signal_action = postgresql.ENUM("BUY", "HOLD", "SELL", name="signal_action", create_type=False)
order_side = postgresql.ENUM("BUY", "SELL", name="order_side", create_type=False)
order_state = postgresql.ENUM(
    "DRAFT",
    "PENDING_APPROVAL",
    "APPROVED",
    "SUBMITTED",
    "OPEN",
    "PARTIALLY_FILLED",
    "FILLED",
    "CANCELLED",
    "REJECTED",
    "FAILED",
    name="order_state",
    create_type=False,
)
candle_interval = postgresql.ENUM("day", "minute", name="candle_interval", create_type=False)
risk_event_type = postgresql.ENUM(
    "LIMIT_BREACH",
    "KILL_SWITCH",
    "STALE_DATA",
    "DUPLICATE_ORDER",
    "RECONCILIATION_MISMATCH",
    name="risk_event_type",
    create_type=False,
)
audit_event_type = postgresql.ENUM(
    "SETTINGS_CHANGE",
    "AUTH",
    "ORDER",
    "RISK",
    "SYSTEM",
    name="audit_event_type",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    signal_action.create(bind, checkfirst=True)
    order_side.create(bind, checkfirst=True)
    order_state.create(bind, checkfirst=True)
    candle_interval.create(bind, checkfirst=True)
    risk_event_type.create(bind, checkfirst=True)
    audit_event_type.create(bind, checkfirst=True)

    op.create_table(
        "instruments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("exchange", sa.String(length=16), nullable=False),
        sa.Column("tradingsymbol", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=True),
        sa.Column("isin", sa.String(length=32), nullable=True),
        sa.Column("instrument_token", sa.BigInteger(), nullable=True),
        sa.Column("lot_size", sa.Integer(), server_default="1", nullable=False),
        sa.Column("tick_size", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("segment", sa.String(length=32), server_default="EQ", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("exchange", "tradingsymbol", name="uq_instruments_exchange_symbol"),
    )
    op.create_index("ix_instruments_tradingsymbol", "instruments", ["tradingsymbol"])

    op.create_table(
        "strategy_runs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("strategy_name", sa.String(length=128), nullable=False),
        sa.Column("strategy_version", sa.String(length=32), nullable=False),
        sa.Column("parameters", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(length=128), nullable=False),
        sa.Column("value_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("key"),
    )

    op.create_table(
        "candles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("instrument_id", sa.UUID(), nullable=False),
        sa.Column("interval", candle_interval, nullable=False),
        sa.Column("candle_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("high", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("low", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("close", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("volume", sa.BigInteger(), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["instrument_id"], ["instruments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "instrument_id",
            "interval",
            "candle_time",
            name="uq_candles_instrument_interval_time",
        ),
    )
    op.create_index("ix_candles_instrument_time", "candles", ["instrument_id", "candle_time"])

    op.create_table(
        "signals",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("strategy_run_id", sa.UUID(), nullable=False),
        sa.Column("instrument_id", sa.UUID(), nullable=False),
        sa.Column("action", signal_action, nullable=False),
        sa.Column("strength", sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column("signal_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("data_as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("entry_price", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("stop_loss", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("target", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("suggested_quantity", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["instrument_id"], ["instruments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["strategy_run_id"], ["strategy_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.create_index("ix_signals_instrument_time", "signals", ["instrument_id", "signal_time"])

    op.create_table(
        "signal_explanations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("signal_id", sa.UUID(), nullable=False),
        sa.Column("reasons_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("narrative", sa.Text(), nullable=True),
        sa.Column("llm_model", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["signal_id"], ["signals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("signal_id"),
    )

    op.create_table(
        "paper_orders",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("instrument_id", sa.UUID(), nullable=False),
        sa.Column("signal_id", sa.UUID(), nullable=True),
        sa.Column("side", order_side, nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("limit_price", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("stop_loss", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("state", order_state, nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("broker_order_id", sa.String(length=64), nullable=True),
        sa.Column("strategy_version", sa.String(length=32), nullable=True),
        sa.Column("fees_estimate", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("filled_quantity", sa.Integer(), nullable=False),
        sa.Column("avg_fill_price", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.ForeignKeyConstraint(["instrument_id"], ["instruments.id"]),
        sa.ForeignKeyConstraint(["signal_id"], ["signals.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.create_index("ix_paper_orders_state", "paper_orders", ["state"])

    op.create_table(
        "live_orders",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("instrument_id", sa.UUID(), nullable=False),
        sa.Column("signal_id", sa.UUID(), nullable=True),
        sa.Column("side", order_side, nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("limit_price", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("stop_loss", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("state", order_state, nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("broker_order_id", sa.String(length=64), nullable=True),
        sa.Column("strategy_version", sa.String(length=32), nullable=True),
        sa.Column("fees_estimate", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("approved_by", sa.String(length=128), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["instrument_id"], ["instruments.id"]),
        sa.ForeignKeyConstraint(["signal_id"], ["signals.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.create_index("ix_live_orders_state", "live_orders", ["state"])

    op.create_table(
        "positions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("instrument_id", sa.UUID(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("avg_price", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("is_paper", sa.Boolean(), nullable=False),
        sa.Column("reconciled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("broker_quantity", sa.Integer(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["instrument_id"], ["instruments.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("instrument_id", "is_paper", name="uq_positions_instrument_paper"),
    )

    op.create_table(
        "portfolio_snapshots",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("snapshot_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_paper", sa.Boolean(), nullable=False),
        sa.Column("cash_balance", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("equity_value", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("total_value", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_portfolio_snapshots_time", "portfolio_snapshots", ["snapshot_time"])

    op.create_table(
        "fills",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("paper_order_id", sa.UUID(), nullable=True),
        sa.Column("live_order_id", sa.UUID(), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("price", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("fees", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("slippage", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("fill_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("broker_trade_id", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["live_order_id"], ["live_orders.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["paper_order_id"], ["paper_orders.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_fills_fill_time", "fills", ["fill_time"])

    op.create_table(
        "risk_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("event_type", risk_event_type, nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("context", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_risk_events_created", "risk_events", ["created_at"])

    op.create_table(
        "audit_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("event_type", audit_event_type, nullable=False),
        sa.Column("actor", sa.String(length=128), nullable=True),
        sa.Column("resource_type", sa.String(length=64), nullable=True),
        sa.Column("resource_id", sa.String(length=64), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_events_created", "audit_events", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_audit_events_created", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index("ix_risk_events_created", table_name="risk_events")
    op.drop_table("risk_events")
    op.drop_index("ix_fills_fill_time", table_name="fills")
    op.drop_table("fills")
    op.drop_index("ix_portfolio_snapshots_time", table_name="portfolio_snapshots")
    op.drop_table("portfolio_snapshots")
    op.drop_table("positions")
    op.drop_index("ix_live_orders_state", table_name="live_orders")
    op.drop_table("live_orders")
    op.drop_index("ix_paper_orders_state", table_name="paper_orders")
    op.drop_table("paper_orders")
    op.drop_table("signal_explanations")
    op.drop_index("ix_signals_instrument_time", table_name="signals")
    op.drop_table("signals")
    op.drop_index("ix_candles_instrument_time", table_name="candles")
    op.drop_table("candles")
    op.drop_table("app_settings")
    op.drop_table("strategy_runs")
    op.drop_index("ix_instruments_tradingsymbol", table_name="instruments")
    op.drop_table("instruments")

    bind = op.get_bind()
    audit_event_type.drop(bind, checkfirst=True)
    risk_event_type.drop(bind, checkfirst=True)
    candle_interval.drop(bind, checkfirst=True)
    order_state.drop(bind, checkfirst=True)
    order_side.drop(bind, checkfirst=True)
    signal_action.drop(bind, checkfirst=True)
