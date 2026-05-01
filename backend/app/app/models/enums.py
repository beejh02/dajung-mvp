from enum import Enum


class UserRole(str, Enum):
    user = "user"
    admin = "admin"


class OrderStatus(str, Enum):
    draft = "draft"
    pending_payment = "pending_payment"
    paid = "paid"
    completed = "completed"
    cancelled = "cancelled"
    failed = "failed"


class PaymentStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    failed = "failed"
    refunded = "refunded"


class OrderSource(str, Enum):
    kiosk_classic = "kiosk_classic"
    kiosk_guided = "kiosk_guided"
    kiosk_premium = "kiosk_premium"
    ai_agent = "ai_agent"
    mcp = "mcp"


class PointLedgerType(str, Enum):
    earn = "earn"
    spend = "spend"
    adjust = "adjust"


class PaymentMethod(str, Enum):
    dummy_card = "dummy_card"
    point = "point"
