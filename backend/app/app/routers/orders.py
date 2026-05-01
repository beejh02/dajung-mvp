from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.dependencies import get_current_user, require_admin_user
from app.db.session import get_session
from app.models import User
from app.schemas.order import OrderCreateRequest, OrderRead, OrderStatusUpdateRequest
from app.services.order_service import (
    create_order,
    get_order_for_user,
    list_user_orders,
    to_order_read,
    transition_order_status,
)

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderRead)
def create_user_order(
    payload: OrderCreateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> OrderRead:
    order = create_order(session, current_user, payload)
    return to_order_read(session, order)


@router.get("/my", response_model=list[OrderRead])
def list_my_orders(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[OrderRead]:
    return [to_order_read(session, order) for order in list_user_orders(session, current_user)]


@router.get("/{order_id}", response_model=OrderRead)
def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> OrderRead:
    order = get_order_for_user(session, order_id, current_user)
    return to_order_read(session, order)


@router.patch("/{order_id}/status", response_model=OrderRead)
def update_order_status(
    order_id: int,
    payload: OrderStatusUpdateRequest,
    _admin_user: User = Depends(require_admin_user),
    session: Session = Depends(get_session),
) -> OrderRead:
    order = get_order_for_user(session, order_id, _admin_user)
    updated_order = transition_order_status(session, order, payload.status)
    return to_order_read(session, updated_order)
