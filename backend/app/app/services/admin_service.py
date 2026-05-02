from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import Order, OrderItem, Payment, PointLedger, Receipt, User
from app.models.enums import OrderSource, OrderStatus, PaymentStatus, PointLedgerType
from app.schemas.admin import (
    AdminOrderDetailRead,
    AdminOrderSourceStatRead,
    AdminOrderSummaryRead,
    AdminOverviewRead,
    AdminPaymentStatusRead,
    AdminPointLedgerEntryRead,
    AdminReceiptStatusRead,
)
from app.schemas.order import OrderItemRead

KST = timezone(timedelta(hours=9))


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _is_today(value: datetime, now: datetime) -> bool:
    return _as_utc(value).astimezone(KST).date() == now.astimezone(KST).date()


def _order_sort_key(order: Order) -> tuple[datetime, int]:
    return (_as_utc(order.created_at), order.id or 0)


def _payment_sort_key(payment: Payment) -> tuple[datetime, int]:
    return (_as_utc(payment.created_at), payment.id or 0)


def _point_ledger_sort_key(entry: PointLedger) -> tuple[datetime, int]:
    return (_as_utc(entry.created_at), entry.id or 0)


def _receipt_sort_key(receipt: Receipt) -> tuple[datetime, int]:
    return (_as_utc(receipt.issued_at), receipt.id or 0)


def _order_ids(orders: list[Order]) -> list[int]:
    return [order.id for order in orders if order.id is not None]


def _get_users_by_id(session: Session, orders: list[Order]) -> dict[str, User]:
    user_ids = sorted({order.user_id for order in orders})
    if not user_ids:
        return {}

    users = session.exec(select(User).where(User.id.in_(user_ids))).all()
    return {user.id: user for user in users}


def _get_payments_by_order_id(session: Session, order_ids: list[int]) -> dict[int, Payment]:
    if not order_ids:
        return {}

    payments = session.exec(select(Payment).where(Payment.order_id.in_(order_ids))).all()
    return {payment.order_id: payment for payment in payments}


def _get_point_ledger_by_order_id(session: Session, order_ids: list[int]) -> dict[int, list[PointLedger]]:
    if not order_ids:
        return {}

    entries = session.exec(select(PointLedger).where(PointLedger.order_id.in_(order_ids))).all()
    grouped: dict[int, list[PointLedger]] = {}
    for entry in entries:
        if entry.order_id is None:
            continue
        grouped.setdefault(entry.order_id, []).append(entry)

    for order_entries in grouped.values():
        order_entries.sort(key=_point_ledger_sort_key, reverse=True)
    return grouped


def _get_receipts_by_order_id(session: Session, order_ids: list[int]) -> dict[int, Receipt]:
    if not order_ids:
        return {}

    receipts = session.exec(select(Receipt).where(Receipt.order_id.in_(order_ids))).all()
    return {receipt.order_id: receipt for receipt in receipts}


def _get_order_items(session: Session, order_id: int) -> list[OrderItem]:
    statement = select(OrderItem).where(OrderItem.order_id == order_id).order_by(OrderItem.id)
    return list(session.exec(statement).all())


def _to_payment_status(payment: Payment) -> AdminPaymentStatusRead:
    return AdminPaymentStatusRead.model_validate(payment)


def _to_point_entry(entry: PointLedger) -> AdminPointLedgerEntryRead:
    return AdminPointLedgerEntryRead.model_validate(entry)


def _to_receipt_status(receipt: Receipt) -> AdminReceiptStatusRead:
    return AdminReceiptStatusRead.model_validate(receipt)


def _earned_points(entries: list[PointLedger]) -> int:
    return sum(entry.amount for entry in entries if entry.type == PointLedgerType.earn)


def _to_order_summary(
    order: Order,
    users_by_id: dict[str, User],
    payments_by_order_id: dict[int, Payment],
    point_ledger_by_order_id: dict[int, list[PointLedger]],
    receipts_by_order_id: dict[int, Receipt],
) -> AdminOrderSummaryRead:
    if order.id is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Order id is missing")

    user = users_by_id.get(order.user_id)
    payment = payments_by_order_id.get(order.id)
    receipt = receipts_by_order_id.get(order.id)
    point_ledger = point_ledger_by_order_id.get(order.id, [])

    return AdminOrderSummaryRead(
        id=order.id,
        user_id=order.user_id,
        user_name=user.name if user is not None else "Unknown user",
        user_email=user.email if user is not None else "",
        source=order.source,
        status=order.status,
        subtotal_amount=order.subtotal_amount,
        discount_amount=order.discount_amount,
        total_amount=order.total_amount,
        created_at=order.created_at,
        updated_at=order.updated_at,
        payment=_to_payment_status(payment) if payment is not None else None,
        earned_points=_earned_points(point_ledger),
        receipt=_to_receipt_status(receipt) if receipt is not None else None,
    )


def _hydrate_order_summaries(session: Session, orders: list[Order]) -> list[AdminOrderSummaryRead]:
    order_ids = _order_ids(orders)
    users_by_id = _get_users_by_id(session, orders)
    payments_by_order_id = _get_payments_by_order_id(session, order_ids)
    point_ledger_by_order_id = _get_point_ledger_by_order_id(session, order_ids)
    receipts_by_order_id = _get_receipts_by_order_id(session, order_ids)

    return [
        _to_order_summary(
            order,
            users_by_id,
            payments_by_order_id,
            point_ledger_by_order_id,
            receipts_by_order_id,
        )
        for order in orders
    ]


def list_admin_orders(session: Session, limit: int = 50) -> list[AdminOrderSummaryRead]:
    orders = list(session.exec(select(Order)).all())
    sorted_orders = sorted(orders, key=_order_sort_key, reverse=True)[:limit]
    return _hydrate_order_summaries(session, sorted_orders)


def get_admin_order_detail(session: Session, order_id: int) -> AdminOrderDetailRead:
    order = session.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    summary = _hydrate_order_summaries(session, [order])[0]
    order_items = [OrderItemRead.model_validate(item) for item in _get_order_items(session, order_id)]
    point_ledger = [
        _to_point_entry(entry)
        for entry in sorted(
            session.exec(select(PointLedger).where(PointLedger.order_id == order_id)).all(),
            key=_point_ledger_sort_key,
            reverse=True,
        )
    ]

    return AdminOrderDetailRead(
        **summary.model_dump(),
        items=order_items,
        point_ledger=point_ledger,
    )


def list_admin_payments(session: Session, limit: int = 100) -> list[AdminPaymentStatusRead]:
    payments = list(session.exec(select(Payment)).all())
    return [
        _to_payment_status(payment)
        for payment in sorted(payments, key=_payment_sort_key, reverse=True)[:limit]
    ]


def list_admin_points(session: Session, limit: int = 100) -> list[AdminPointLedgerEntryRead]:
    entries = list(session.exec(select(PointLedger)).all())
    return [
        _to_point_entry(entry)
        for entry in sorted(entries, key=_point_ledger_sort_key, reverse=True)[:limit]
    ]


def list_admin_receipts(session: Session, limit: int = 100) -> list[AdminReceiptStatusRead]:
    receipts = list(session.exec(select(Receipt)).all())
    return [
        _to_receipt_status(receipt)
        for receipt in sorted(receipts, key=_receipt_sort_key, reverse=True)[:limit]
    ]


def get_admin_overview(session: Session, recent_order_limit: int = 10) -> AdminOverviewRead:
    now = datetime.now(timezone.utc)
    orders = list(session.exec(select(Order)).all())
    payments = list(session.exec(select(Payment)).all())
    point_entries = list(session.exec(select(PointLedger)).all())
    receipts = list(session.exec(select(Receipt)).all())

    payments_by_order_id = {payment.order_id: payment for payment in payments}
    today_orders = [order for order in orders if _is_today(order.created_at, now)]
    approved_payments = [payment for payment in payments if payment.status == PaymentStatus.approved]
    today_approved_payments = [
        payment
        for payment in approved_payments
        if payment.approved_at is not None and _is_today(payment.approved_at, now)
    ]

    source_stats: list[AdminOrderSourceStatRead] = []
    for source in OrderSource:
        source_orders = [order for order in orders if order.source == source]
        paid_source_payments: list[Payment] = []
        for order in source_orders:
            if order.id is None:
                continue
            payment = payments_by_order_id.get(order.id)
            if payment is not None and payment.status == PaymentStatus.approved:
                paid_source_payments.append(payment)

        source_stats.append(
            AdminOrderSourceStatRead(
                source=source,
                order_count=len(source_orders),
                paid_order_count=len(paid_source_payments),
                sales_amount=sum(payment.approved_amount for payment in paid_source_payments),
            )
        )

    recent_orders = sorted(orders, key=_order_sort_key, reverse=True)[:recent_order_limit]
    earned_points_total = sum(
        entry.amount for entry in point_entries if entry.type == PointLedgerType.earn
    )

    return AdminOverviewRead(
        today_order_count=len(today_orders),
        today_dummy_sales_amount=sum(payment.approved_amount for payment in today_approved_payments),
        total_order_count=len(orders),
        total_dummy_sales_amount=sum(payment.approved_amount for payment in approved_payments),
        pending_payment_count=len([order for order in orders if order.status == OrderStatus.pending_payment]),
        paid_order_count=len([order for order in orders if order.status in {OrderStatus.paid, OrderStatus.completed}]),
        failed_order_count=len([order for order in orders if order.status == OrderStatus.failed]),
        receipt_issued_count=len(receipts),
        earned_points_total=earned_points_total,
        source_stats=source_stats,
        recent_orders=_hydrate_order_summaries(session, recent_orders),
    )
