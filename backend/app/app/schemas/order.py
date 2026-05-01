from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import OrderSource, OrderStatus


class SelectedOptionInput(BaseModel):
    group_id: str
    choice_ids: list[str]


class OrderCreateItem(BaseModel):
    menu_item_id: str
    quantity: int = Field(gt=0)
    selected_options: list[SelectedOptionInput] = Field(default_factory=list)


class OrderCreateRequest(BaseModel):
    source: OrderSource
    items: list[OrderCreateItem] = Field(min_length=1)


class OrderItemRead(BaseModel):
    id: int
    menu_item_id: str
    name_snapshot: str
    unit_price: int
    quantity: int
    selected_options: list[dict[str, Any]]
    line_total: int


class OrderRead(BaseModel):
    id: int
    user_id: str
    source: OrderSource
    status: OrderStatus
    subtotal_amount: int
    discount_amount: int
    total_amount: int
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemRead] = Field(default_factory=list)
