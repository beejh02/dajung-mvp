from datetime import datetime

from pydantic import BaseModel

from app.models.enums import PaymentMethod, PaymentStatus


class DummyPaymentApproveRequest(BaseModel):
    order_id: int
    idempotency_key: str | None = None


class PaymentRead(BaseModel):
    id: int
    order_id: int
    status: PaymentStatus
    method: PaymentMethod
    approved_amount: int
    dummy_approval_code: str | None = None
    approved_at: datetime | None = None
