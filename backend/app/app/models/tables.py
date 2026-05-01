from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, Column, UniqueConstraint
from sqlmodel import Field, SQLModel

from app.models.enums import (
    OrderSource,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
    PointLedgerType,
    UserRole,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", name="uq_users_email"),)

    id: str = Field(primary_key=True)
    email: str = Field(index=True)
    password_hash: str
    name: str
    phone: str | None = None
    role: UserRole = Field(default=UserRole.user, index=True)
    points_balance: int = Field(default=0)
    created_at: datetime = Field(default_factory=utc_now)


class AgentHandoffToken(SQLModel, table=True):
    __tablename__ = "agent_handoff_tokens"
    __table_args__ = (UniqueConstraint("token_hash", name="uq_agent_handoff_tokens_token_hash"),)

    id: int | None = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    token_hash: str = Field(index=True)
    expires_at: datetime
    used_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now)


class MenuItem(SQLModel, table=True):
    __tablename__ = "menu_items"

    id: str = Field(primary_key=True)
    brand_id: str | None = Field(default=None, index=True)
    name: str = Field(index=True)
    category: str = Field(index=True)
    description: str | None = None
    price: int
    image_url: str | None = None
    is_available: bool = Field(default=True, index=True)
    ingredients: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    options: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))


class Order(SQLModel, table=True):
    __tablename__ = "orders"

    id: int | None = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    source: OrderSource = Field(index=True)
    status: OrderStatus = Field(default=OrderStatus.draft, index=True)
    subtotal_amount: int = Field(default=0)
    discount_amount: int = Field(default=0)
    total_amount: int = Field(default=0)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class OrderItem(SQLModel, table=True):
    __tablename__ = "order_items"

    id: int | None = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id", index=True)
    menu_item_id: str = Field(foreign_key="menu_items.id", index=True)
    name_snapshot: str
    unit_price: int
    quantity: int
    selected_options: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    line_total: int


class Payment(SQLModel, table=True):
    __tablename__ = "payments"
    __table_args__ = (
        UniqueConstraint("order_id", name="uq_payments_order_id"),
        UniqueConstraint("idempotency_key", name="uq_payments_idempotency_key"),
        UniqueConstraint("dummy_approval_code", name="uq_payments_dummy_approval_code"),
    )

    id: int | None = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id", index=True)
    status: PaymentStatus = Field(default=PaymentStatus.pending, index=True)
    method: PaymentMethod = Field(default=PaymentMethod.dummy_card)
    approved_amount: int = Field(default=0)
    idempotency_key: str | None = Field(default=None, index=True)
    dummy_approval_code: str | None = Field(default=None)
    approved_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now)


class PointLedger(SQLModel, table=True):
    __tablename__ = "point_ledger"
    __table_args__ = (
        UniqueConstraint("user_id", "order_id", "type", name="uq_point_ledger_user_order_type"),
        UniqueConstraint("idempotency_key", name="uq_point_ledger_idempotency_key"),
    )

    id: int | None = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    order_id: int | None = Field(default=None, foreign_key="orders.id", index=True)
    type: PointLedgerType = Field(index=True)
    amount: int
    balance_after: int
    idempotency_key: str | None = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=utc_now)


class Receipt(SQLModel, table=True):
    __tablename__ = "receipts"
    __table_args__ = (
        UniqueConstraint("order_id", name="uq_receipts_order_id"),
        UniqueConstraint("receipt_number", name="uq_receipts_receipt_number"),
        UniqueConstraint("idempotency_key", name="uq_receipts_idempotency_key"),
    )

    id: int | None = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id", index=True)
    receipt_number: str = Field(index=True)
    content: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    idempotency_key: str | None = Field(default=None, index=True)
    issued_at: datetime = Field(default_factory=utc_now)
