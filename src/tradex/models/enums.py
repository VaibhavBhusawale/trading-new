import enum


class SignalAction(str, enum.Enum):
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"


class OrderSide(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderState(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    SUBMITTED = "SUBMITTED"
    OPEN = "OPEN"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class CandleInterval(str, enum.Enum):
    DAY = "day"
    MINUTE = "minute"


class RiskEventType(str, enum.Enum):
    LIMIT_BREACH = "LIMIT_BREACH"
    KILL_SWITCH = "KILL_SWITCH"
    STALE_DATA = "STALE_DATA"
    DUPLICATE_ORDER = "DUPLICATE_ORDER"
    RECONCILIATION_MISMATCH = "RECONCILIATION_MISMATCH"


class AuditEventType(str, enum.Enum):
    SETTINGS_CHANGE = "SETTINGS_CHANGE"
    AUTH = "AUTH"
    ORDER = "ORDER"
    RISK = "RISK"
    SYSTEM = "SYSTEM"
    BROKER = "BROKER"


class BrokerProvider(str, enum.Enum):
    MOCK = "mock"
    ZERODHA = "zerodha"
    ANGEL_ONE = "angel_one"
    UPSTOX = "upstox"


class BrokerAccountStatus(str, enum.Enum):
    DRAFT = "draft"
    CONFIGURED = "configured"
    SESSION_EXPIRED = "session_expired"
    ERROR = "error"
