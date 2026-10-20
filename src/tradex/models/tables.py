import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from tradex.db.base import Base
from tradex.models.enums import (
    AuditEventType,
    BrokerAccountStatus,
    BrokerProvider,
    CandleInterval,
    OrderSide,
    OrderState,
    RiskEventType,
    SignalAction,
)


class Instrument(Base):
    __tablename__ = "instruments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exchange: Mapped[str] = mapped_column(String(16), nullable=False, default="NSE")
    tradingsymbol: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str | None] = mapped_column(String(256))
    isin: Mapped[str | None] = mapped_column(String(32))
    instrument_token: Mapped[int | None] = mapped_column(BigInteger)
    lot_size: Mapped[int] = mapped_column(default=1)
    tick_size: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    segment: Mapped[str] = mapped_column(String(32), default="EQ")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    candles: Mapped[list["Candle"]] = relationship(back_populates="instrument")

    __table_args__ = (
        UniqueConstraint("exchange", "tradingsymbol", name="uq_instruments_exchange_symbol"),
        Index("ix_instruments_tradingsymbol", "tradingsymbol"),
    )


class Candle(Base):
    __tablename__ = "candles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("instruments.id", ondelete="CASCADE"),
        nullable=False,
    )
    interval: Mapped[CandleInterval] = mapped_column(Enum(CandleInterval, name="candle_interval"))
    candle_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    open: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="mock")
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    instrument: Mapped[Instrument] = relationship(back_populates="candles")

    __table_args__ = (
        UniqueConstraint(
            "instrument_id",
            "interval",
            "candle_time",
            name="uq_candles_instrument_interval_time",
        ),
        Index("ix_candles_instrument_time", "instrument_id", "candle_time"),
    )


class StrategyRun(Base):
    __tablename__ = "strategy_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    strategy_name: Mapped[str] = mapped_column(String(128), nullable=False)
    strategy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    parameters: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), default="running")
    notes: Mapped[str | None] = mapped_column(Text)

    signals: Mapped[list["Signal"]] = relationship(back_populates="strategy_run")


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    strategy_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("strategy_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("instruments.id", ondelete="CASCADE"),
        nullable=False,
    )
    action: Mapped[SignalAction] = mapped_column(Enum(SignalAction, name="signal_action"))
    strength: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    signal_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    data_as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    entry_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    stop_loss: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    target: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    suggested_quantity: Mapped[int | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    strategy_run: Mapped[StrategyRun] = relationship(back_populates="signals")
    instrument: Mapped[Instrument] = relationship()
    explanation: Mapped["SignalExplanation | None"] = relationship(
        back_populates="signal",
        uselist=False,
    )

    __table_args__ = (Index("ix_signals_instrument_time", "instrument_id", "signal_time"),)


class SignalExplanation(Base):
    __tablename__ = "signal_explanations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    signal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("signals.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    reasons_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    narrative: Mapped[str | None] = mapped_column(Text)
    llm_model: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    signal: Mapped[Signal] = relationship(back_populates="explanation")


class _OrderColumns:
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("instruments.id"),
        nullable=False,
    )
    signal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("signals.id"),
    )
    side: Mapped[OrderSide] = mapped_column(Enum(OrderSide, name="order_side"))
    quantity: Mapped[int] = mapped_column(nullable=False)
    limit_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    stop_loss: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    state: Mapped[OrderState] = mapped_column(
        Enum(OrderState, name="order_state"),
        default=OrderState.DRAFT,
    )
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    broker_order_id: Mapped[str | None] = mapped_column(String(64))
    strategy_version: Mapped[str | None] = mapped_column(String(32))
    fees_estimate: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PaperOrder(Base, _OrderColumns):
    __tablename__ = "paper_orders"

    filled_quantity: Mapped[int] = mapped_column(default=0)
    avg_fill_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))

    __table_args__ = (Index("ix_paper_orders_state", "state"),)


class LiveOrder(Base, _OrderColumns):
    __tablename__ = "live_orders"

    approved_by: Mapped[str | None] = mapped_column(String(128))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejection_reason: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (Index("ix_live_orders_state", "state"),)


class Fill(Base):
    __tablename__ = "fills"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("paper_orders.id", ondelete="SET NULL"),
    )
    live_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("live_orders.id", ondelete="SET NULL"),
    )
    quantity: Mapped[int] = mapped_column(nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    fees: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))
    slippage: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))
    fill_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String(32), default="mock")
    broker_trade_id: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (Index("ix_fills_fill_time", "fill_time"),)


class Position(Base):
    __tablename__ = "positions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("instruments.id"),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(nullable=False, default=0)
    avg_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    is_paper: Mapped[bool] = mapped_column(Boolean, default=True)
    reconciled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    broker_quantity: Mapped[int | None] = mapped_column()
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("instrument_id", "is_paper", name="uq_positions_instrument_paper"),
    )


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_paper: Mapped[bool] = mapped_column(Boolean, default=True)
    cash_balance: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    equity_value: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    total_value: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (Index("ix_portfolio_snapshots_time", "snapshot_time"),)


class RiskEvent(Base):
    __tablename__ = "risk_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type: Mapped[RiskEventType] = mapped_column(
        Enum(RiskEventType, name="risk_event_type"),
        nullable=False,
    )
    severity: Mapped[str] = mapped_column(String(16), default="warning")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (Index("ix_risk_events_created", "created_at"),)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type: Mapped[AuditEventType] = mapped_column(
        Enum(AuditEventType, name="audit_event_type"),
        nullable=False,
    )
    actor: Mapped[str | None] = mapped_column(String(128))
    resource_type: Mapped[str | None] = mapped_column(String(64))
    resource_id: Mapped[str | None] = mapped_column(String(64))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (Index("ix_audit_events_created", "created_at"),)


class AppSetting(Base):
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    schema_version: Mapped[int] = mapped_column(default=1)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class BrokerAccount(Base):
    """Broker credentials managed from the UI; secrets stored encrypted."""

    __tablename__ = "broker_accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    provider: Mapped[BrokerProvider] = mapped_column(
        Enum(BrokerProvider, name="broker_provider"),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[BrokerAccountStatus] = mapped_column(
        Enum(BrokerAccountStatus, name="broker_account_status"),
        nullable=False,
        default=BrokerAccountStatus.DRAFT,
    )
    credentials_encrypted: Mapped[str | None] = mapped_column(Text)
    public_meta: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        Index("ix_broker_accounts_provider", "provider"),
        Index("ix_broker_accounts_active", "is_active"),
    )
