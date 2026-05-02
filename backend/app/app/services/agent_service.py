from fastapi import HTTPException, status
from sqlmodel import Session

from app.models import User
from app.models.enums import OrderSource
from app.schemas.agent import (
    AgentMenuRead,
    AgentOrderConfirmRequest,
    AgentOrderDraftRead,
    AgentOrderDraftRequest,
    AgentPaymentApproveRead,
    AgentPaymentApproveRequest,
    AgentUserContextRead,
)
from app.schemas.menu import MenuItemRead
from app.schemas.order import OrderCreateRequest, OrderItemRead, OrderRead
from app.schemas.payment import PaymentRead
from app.schemas.points import PointBalanceRead
from app.schemas.receipt import ReceiptRead
from app.schemas.user import UserRead
from app.services.menu_service import list_menu_items
from app.services.order_service import create_order, list_user_orders, price_order, to_order_read
from app.services.payment_service import approve_dummy_payment
from app.services.receipt_service import get_order_receipt_for_user


def _to_ai_agent_order_request(payload: AgentOrderDraftRequest) -> OrderCreateRequest:
    return OrderCreateRequest(
        source=OrderSource.ai_agent,
        items=payload.items,
        simulate_failure=payload.simulate_failure,
    )


def get_agent_menu(session: Session) -> AgentMenuRead:
    return AgentMenuRead(items=[MenuItemRead.model_validate(item) for item in list_menu_items(session)])


def get_agent_user_context(session: Session, user: User) -> AgentUserContextRead:
    recent_orders = list_user_orders(session, user)[:5]
    return AgentUserContextRead(
        user=UserRead.model_validate(user),
        points=PointBalanceRead(user_id=user.id, points_balance=user.points_balance),
        recent_orders=[to_order_read(session, order) for order in recent_orders],
    )


def create_agent_order_draft(session: Session, payload: AgentOrderDraftRequest) -> AgentOrderDraftRead:
    priced_order = price_order(session, _to_ai_agent_order_request(payload))
    return AgentOrderDraftRead(
        subtotal_amount=priced_order.subtotal_amount,
        discount_amount=priced_order.discount_amount,
        total_amount=priced_order.total_amount,
        items=[
            OrderItemRead(
                id=index,
                menu_item_id=item.menu_item_id,
                name_snapshot=item.name_snapshot,
                unit_price=item.unit_price,
                quantity=item.quantity,
                selected_options=item.selected_options,
                line_total=item.line_total,
            )
            for index, item in enumerate(priced_order.items, start=1)
        ],
    )


def confirm_agent_order(session: Session, user: User, payload: AgentOrderConfirmRequest) -> OrderRead:
    order = create_order(session, user, _to_ai_agent_order_request(payload))
    return to_order_read(session, order)


def approve_agent_dummy_payment(
    session: Session,
    user: User,
    payload: AgentPaymentApproveRequest,
) -> AgentPaymentApproveRead:
    payment = approve_dummy_payment(session, user, payload)
    receipt = None
    if payment.order_id is not None:
        try:
            receipt = ReceiptRead.model_validate(get_order_receipt_for_user(session, payment.order_id, user))
        except HTTPException as exc:
            if exc.status_code != status.HTTP_404_NOT_FOUND:
                raise

    session.refresh(user)
    return AgentPaymentApproveRead(
        payment=PaymentRead.model_validate(payment),
        points=PointBalanceRead(user_id=user.id, points_balance=user.points_balance),
        receipt=receipt,
    )
