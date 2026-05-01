from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.core.security import utc_now
from app.models import Order, OrderItem, Payment, PointLedger, Receipt, User
from app.models.enums import OrderStatus, PaymentStatus, PointLedgerType
from app.schemas.payment import DummyPaymentApproveRequest
from app.services.order_service import user_can_access_order
from app.services.points_service import calculate_earn_points
from app.services.receipt_service import build_receipt_content


def _conflict(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)


def _get_existing_payment(session: Session, order_id: int) -> Payment | None:
    return session.exec(select(Payment).where(Payment.order_id == order_id)).first()


def _get_order_items(session: Session, order_id: int) -> list[OrderItem]:
    statement = select(OrderItem).where(OrderItem.order_id == order_id).order_by(OrderItem.id)
    return list(session.exec(statement).all())


def approve_dummy_payment(session: Session, user: User, payload: DummyPaymentApproveRequest) -> Payment:
    order = session.get(Order, payload.order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if not user_can_access_order(user, order):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Payment access denied")
    order_user = session.get(User, order.user_id)
    if order_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order user not found")

    if payload.idempotency_key:
        payment_for_key = session.exec(
            select(Payment).where(Payment.idempotency_key == payload.idempotency_key)
        ).first()
        if payment_for_key is not None:
            if payment_for_key.order_id != order.id:
                raise _conflict("Idempotency key was used for a different order")
            return payment_for_key

    existing_payment = _get_existing_payment(session, order.id)
    if existing_payment is not None:
        return existing_payment

    if order.status != OrderStatus.pending_payment:
        raise _conflict(f"Order is not awaiting payment: {order.status.value}")

    now = utc_now()
    idempotency_key = payload.idempotency_key or f"dummy-payment:order:{order.id}"
    try:
        if payload.simulate_failure:
            payment = Payment(
                order_id=order.id,
                status=PaymentStatus.failed,
                approved_amount=0,
                idempotency_key=idempotency_key,
                dummy_approval_code=f"DUMMY-FAIL-{order.id:08d}",
                approved_at=None,
                created_at=now,
            )
            order.status = OrderStatus.failed
            order.updated_at = now
            session.add(order)
            session.add(payment)
            session.commit()
            session.refresh(payment)
            return payment

        payment = Payment(
            order_id=order.id,
            status=PaymentStatus.approved,
            approved_amount=order.total_amount,
            idempotency_key=idempotency_key,
            dummy_approval_code=f"DUMMY-APPROVED-{order.id:08d}",
            approved_at=now,
            created_at=now,
        )
        session.add(payment)
        session.flush()

        order.status = OrderStatus.paid
        order.updated_at = now
        session.add(order)

        order_user.points_balance += calculate_earn_points(order.total_amount)
        point_ledger = PointLedger(
            user_id=order_user.id,
            order_id=order.id,
            type=PointLedgerType.earn,
            amount=calculate_earn_points(order.total_amount),
            balance_after=order_user.points_balance,
            idempotency_key=f"point-ledger:earn:order:{order.id}",
            created_at=now,
        )
        session.add(order_user)
        session.add(point_ledger)

        receipt = Receipt(
            order_id=order.id,
            receipt_number=f"R-{order.id:08d}",
            content=build_receipt_content(order, _get_order_items(session, order.id), payment, point_ledger.amount),
            idempotency_key=f"receipt:order:{order.id}",
            issued_at=now,
        )
        session.add(receipt)
        session.commit()
        session.refresh(payment)
        return payment
    except IntegrityError:
        session.rollback()
        existing_payment = _get_existing_payment(session, order.id)
        if existing_payment is not None:
            return existing_payment
        raise


def get_payment_for_user(session: Session, payment_id: int, user: User) -> Payment:
    payment = session.get(Payment, payment_id)
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    order = session.get(Order, payment.order_id)
    if order is None or not user_can_access_order(user, order):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Payment access denied")
    return payment
