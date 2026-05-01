from typing import Any

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import Order, OrderItem, Payment, Receipt, User
from app.services.order_service import user_can_access_order


def build_receipt_content(order: Order, order_items: list[OrderItem], payment: Payment, earned_points: int) -> dict[str, Any]:
    return {
        "order_id": order.id,
        "user_id": order.user_id,
        "source": order.source.value,
        "status": order.status.value,
        "subtotal_amount": order.subtotal_amount,
        "discount_amount": order.discount_amount,
        "total_amount": order.total_amount,
        "payment": {
            "id": payment.id,
            "method": payment.method.value,
            "status": payment.status.value,
            "approved_amount": payment.approved_amount,
            "dummy_approval_code": payment.dummy_approval_code,
        },
        "earned_points": earned_points,
        "items": [
            {
                "menu_item_id": item.menu_item_id,
                "name": item.name_snapshot,
                "unit_price": item.unit_price,
                "quantity": item.quantity,
                "selected_options": item.selected_options,
                "line_total": item.line_total,
            }
            for item in order_items
        ],
    }


def get_receipt_for_user(session: Session, receipt_id: int, user: User) -> Receipt:
    receipt = session.get(Receipt, receipt_id)
    if receipt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found")

    order = session.get(Order, receipt.order_id)
    if order is None or not user_can_access_order(user, order):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Receipt access denied")
    return receipt


def get_order_receipt_for_user(session: Session, order_id: int, user: User) -> Receipt:
    order = session.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if not user_can_access_order(user, order):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Receipt access denied")

    receipt = session.exec(select(Receipt).where(Receipt.order_id == order_id)).first()
    if receipt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found")
    return receipt
