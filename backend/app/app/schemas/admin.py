from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    OrderSource,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
    PointLedgerType,
)
from app.schemas.order import OrderItemRead


class AdminPaymentStatusRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    status: PaymentStatus
    method: PaymentMethod
    approved_amount: int
    dummy_approval_code: str | None = None
    approved_at: datetime | None = None
    created_at: datetime


class AdminPointLedgerEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: str
    order_id: int | None = None
    type: PointLedgerType
    amount: int
    balance_after: int
    created_at: datetime


class AdminReceiptStatusRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    receipt_number: str
    issued_at: datetime


class AdminOrderSummaryRead(BaseModel):
    id: int
    user_id: str
    user_name: str
    user_email: str
    source: OrderSource
    status: OrderStatus
    subtotal_amount: int
    discount_amount: int
    total_amount: int
    created_at: datetime
    updated_at: datetime
    payment: AdminPaymentStatusRead | None = None
    earned_points: int = 0
    receipt: AdminReceiptStatusRead | None = None


class AdminOrderDetailRead(AdminOrderSummaryRead):
    items: list[OrderItemRead] = Field(default_factory=list)
    point_ledger: list[AdminPointLedgerEntryRead] = Field(default_factory=list)


class AdminOrderSourceStatRead(BaseModel):
    source: OrderSource
    order_count: int
    paid_order_count: int
    sales_amount: int


class AdminOverviewRead(BaseModel):
    today_order_count: int
    today_dummy_sales_amount: int
    total_order_count: int
    total_dummy_sales_amount: int
    pending_payment_count: int
    paid_order_count: int
    failed_order_count: int
    receipt_issued_count: int
    earned_points_total: int
    source_stats: list[AdminOrderSourceStatRead] = Field(default_factory=list)
    recent_orders: list[AdminOrderSummaryRead] = Field(default_factory=list)
