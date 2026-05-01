from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ReceiptRead(BaseModel):
    id: int
    order_id: int
    receipt_number: str
    content: dict[str, Any]
    issued_at: datetime
