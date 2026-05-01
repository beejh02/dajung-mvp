from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.core.security import utc_now
from app.models import MenuItem, Order, OrderItem, User
from app.models.enums import OrderStatus, UserRole
from app.schemas.order import OrderCreateItem, OrderCreateRequest, OrderItemRead, OrderRead


@dataclass(frozen=True)
class PricedOrderItem:
    menu_item_id: str
    name_snapshot: str
    unit_price: int
    quantity: int
    selected_options: list[dict]
    line_total: int


@dataclass(frozen=True)
class PricedOrder:
    items: list[PricedOrderItem]
    subtotal_amount: int
    discount_amount: int
    total_amount: int


ALLOWED_STATUS_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.draft: {OrderStatus.pending_payment, OrderStatus.cancelled},
    OrderStatus.pending_payment: {OrderStatus.paid, OrderStatus.cancelled, OrderStatus.failed},
    OrderStatus.paid: {OrderStatus.completed, OrderStatus.cancelled},
    OrderStatus.completed: set(),
    OrderStatus.cancelled: set(),
    OrderStatus.failed: set(),
}


def _bad_request(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def _not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def _forbidden(detail: str = "Order access denied") -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def _choice_map(group: dict) -> dict[str, dict]:
    return {choice["id"]: choice for choice in group.get("choices", [])}


def _selected_groups(item: OrderCreateItem) -> dict[str, list[str]]:
    selected: dict[str, list[str]] = {}
    for group_selection in item.selected_options:
        if group_selection.group_id in selected:
            raise _bad_request(f"Duplicate option group selected: {group_selection.group_id}")
        if len(set(group_selection.choice_ids)) != len(group_selection.choice_ids):
            raise _bad_request(f"Duplicate option choice selected in group: {group_selection.group_id}")
        selected[group_selection.group_id] = group_selection.choice_ids
    return selected


def price_order(session: Session, payload: OrderCreateRequest) -> PricedOrder:
    if payload.simulate_failure:
        raise _bad_request("Dummy order failure requested")

    priced_items: list[PricedOrderItem] = []
    subtotal = 0

    for item in payload.items:
        menu_item = session.get(MenuItem, item.menu_item_id)
        if menu_item is None:
            raise _bad_request(f"Menu item not found: {item.menu_item_id}")
        if not menu_item.is_available:
            raise _bad_request(f"Menu item is not available: {item.menu_item_id}")

        selected = _selected_groups(item)
        option_groups = {group["id"]: group for group in menu_item.options}

        unknown_groups = set(selected) - set(option_groups)
        if unknown_groups:
            raise _bad_request(f"Unknown option group: {sorted(unknown_groups)[0]}")

        option_total = 0
        selected_snapshot: list[dict] = []
        for group in menu_item.options:
            group_id = group["id"]
            choice_ids = selected.get(group_id, [])
            choice_count = len(choice_ids)
            min_select = int(group.get("min_select", 0))
            max_select = int(group.get("max_select", 0))

            if group.get("required", False) and choice_count == 0:
                raise _bad_request(f"Required option group missing: {group_id}")
            if choice_count < min_select:
                raise _bad_request(f"Too few option choices for group: {group_id}")
            if choice_count > max_select:
                raise _bad_request(f"Too many option choices for group: {group_id}")

            choices = _choice_map(group)
            selected_choices: list[dict] = []
            for choice_id in choice_ids:
                choice = choices.get(choice_id)
                if choice is None:
                    raise _bad_request(f"Unknown option choice: {choice_id}")
                if not choice.get("is_available", True):
                    raise _bad_request(f"Option choice is not available: {choice_id}")

                price_delta = int(choice.get("price_delta", 0))
                option_total += price_delta
                selected_choices.append(
                    {
                        "id": choice["id"],
                        "name": choice["name"],
                        "price_delta": price_delta,
                    }
                )

            if selected_choices:
                selected_snapshot.append(
                    {
                        "group_id": group_id,
                        "group_name": group["name"],
                        "choices": selected_choices,
                    }
                )

        unit_price = menu_item.price + option_total
        line_total = unit_price * item.quantity
        subtotal += line_total
        priced_items.append(
            PricedOrderItem(
                menu_item_id=menu_item.id,
                name_snapshot=menu_item.name,
                unit_price=unit_price,
                quantity=item.quantity,
                selected_options=selected_snapshot,
                line_total=line_total,
            )
        )

    return PricedOrder(
        items=priced_items,
        subtotal_amount=subtotal,
        discount_amount=0,
        total_amount=subtotal,
    )


def create_order(session: Session, user: User, payload: OrderCreateRequest) -> Order:
    priced_order = price_order(session, payload)
    now = utc_now()
    order = Order(
        user_id=user.id,
        source=payload.source,
        status=OrderStatus.pending_payment,
        subtotal_amount=priced_order.subtotal_amount,
        discount_amount=priced_order.discount_amount,
        total_amount=priced_order.total_amount,
        created_at=now,
        updated_at=now,
    )
    session.add(order)
    session.flush()

    for priced_item in priced_order.items:
        session.add(
            OrderItem(
                order_id=order.id,
                menu_item_id=priced_item.menu_item_id,
                name_snapshot=priced_item.name_snapshot,
                unit_price=priced_item.unit_price,
                quantity=priced_item.quantity,
                selected_options=priced_item.selected_options,
                line_total=priced_item.line_total,
            )
        )

    session.commit()
    session.refresh(order)
    return order


def user_can_access_order(user: User, order: Order) -> bool:
    return user.role == UserRole.admin or order.user_id == user.id


def get_order_for_user(session: Session, order_id: int, user: User) -> Order:
    order = session.get(Order, order_id)
    if order is None:
        raise _not_found("Order not found")
    if not user_can_access_order(user, order):
        raise _forbidden()
    return order


def list_user_orders(session: Session, user: User) -> list[Order]:
    statement = select(Order).where(Order.user_id == user.id).order_by(Order.created_at.desc())
    return list(session.exec(statement).all())


def transition_order_status(session: Session, order: Order, target_status: OrderStatus) -> Order:
    if target_status == order.status:
        return order

    allowed_targets = ALLOWED_STATUS_TRANSITIONS[order.status]
    if target_status not in allowed_targets:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invalid order status transition: {order.status.value} -> {target_status.value}",
        )

    order.status = target_status
    order.updated_at = utc_now()
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


def get_order_items(session: Session, order_id: int) -> list[OrderItem]:
    statement = select(OrderItem).where(OrderItem.order_id == order_id).order_by(OrderItem.id)
    return list(session.exec(statement).all())


def to_order_read(session: Session, order: Order) -> OrderRead:
    return OrderRead(
        id=order.id,
        user_id=order.user_id,
        source=order.source,
        status=order.status,
        subtotal_amount=order.subtotal_amount,
        discount_amount=order.discount_amount,
        total_amount=order.total_amount,
        created_at=order.created_at,
        updated_at=order.updated_at,
        items=[
            OrderItemRead.model_validate(order_item)
            for order_item in get_order_items(session, order.id)
        ],
    )
