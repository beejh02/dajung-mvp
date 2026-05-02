from pydantic import BaseModel, Field

from app.models.enums import OrderSource
from app.schemas.menu import MenuItemRead
from app.schemas.order import OrderCreateItem, OrderItemRead, OrderRead
from app.schemas.payment import DummyPaymentApproveRequest, PaymentRead
from app.schemas.points import PointBalanceRead
from app.schemas.receipt import ReceiptRead
from app.schemas.user import UserRead


class AgentOrderDraftRequest(BaseModel):
    items: list[OrderCreateItem] = Field(min_length=1)
    simulate_failure: bool = False


class AgentOrderConfirmRequest(AgentOrderDraftRequest):
    pass


class AgentOrderDraftRead(BaseModel):
    source: OrderSource = OrderSource.ai_agent
    subtotal_amount: int
    discount_amount: int
    total_amount: int
    items: list[OrderItemRead] = Field(default_factory=list)


class AgentUserContextRead(BaseModel):
    user: UserRead
    points: PointBalanceRead
    recent_orders: list[OrderRead] = Field(default_factory=list)


class AgentMenuRead(BaseModel):
    items: list[MenuItemRead] = Field(default_factory=list)


class AgentPaymentApproveRequest(DummyPaymentApproveRequest):
    pass


class AgentPaymentApproveRead(BaseModel):
    payment: PaymentRead
    points: PointBalanceRead
    receipt: ReceiptRead | None = None
