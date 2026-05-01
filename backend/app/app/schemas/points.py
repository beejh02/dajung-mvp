from datetime import datetime

from pydantic import BaseModel

from app.models.enums import PointLedgerType


class PointBalanceRead(BaseModel):
    user_id: str
    points_balance: int


class PointLedgerRead(BaseModel):
    id: int
    user_id: str
    order_id: int | None = None
    type: PointLedgerType
    amount: int
    balance_after: int
    created_at: datetime
