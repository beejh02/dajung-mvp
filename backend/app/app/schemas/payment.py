from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import PaymentMethod, PaymentStatus


class DummyPaymentApproveRequest(BaseModel):
    order_id: int
    idempotency_key: str | None = None
    simulate_failure: bool = False


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    status: PaymentStatus
    method: PaymentMethod
    approved_amount: int
    dummy_approval_code: str | None = None
    approved_at: datetime | None = None
