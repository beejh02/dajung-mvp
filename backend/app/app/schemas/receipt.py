from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ReceiptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    receipt_number: str
    content: dict[str, Any]
    issued_at: datetime
