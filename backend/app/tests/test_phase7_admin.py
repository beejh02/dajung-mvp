import pytest
from fastapi import HTTPException
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.dependencies import require_admin_user
from app.models import MenuItem, User
from app.models.enums import OrderSource, PaymentStatus, UserRole
from app.schemas.order import OrderCreateRequest
from app.schemas.payment import DummyPaymentApproveRequest
from app.services.admin_service import get_admin_order_detail, get_admin_overview, list_admin_orders
from app.services.order_service import create_order
from app.services.payment_service import approve_dummy_payment


@pytest.fixture()
def session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(
            User(
                id="user_test",
                email="test@example.test",
                password_hash="pbkdf2_sha256$1$c2FsdA$ZGlnZXN0",
                name="Test User",
                role=UserRole.user,
            )
        )
        session.add(
            User(
                id="admin_test",
                email="admin@example.test",
                password_hash="pbkdf2_sha256$1$c2FsdA$ZGlnZXN0",
                name="Admin User",
                role=UserRole.admin,
            )
        )
        session.add(
            MenuItem(
                id="menu_test_set",
                name="Test Set",
                category="set",
                price=1200,
                is_available=True,
                options=[],
            )
        )
        session.commit()
        yield session


def _order_payload(source: OrderSource, quantity: int = 1) -> OrderCreateRequest:
    return OrderCreateRequest.model_validate(
        {
            "source": source,
            "items": [{"menu_item_id": "menu_test_set", "quantity": quantity, "selected_options": []}],
        }
    )


def test_admin_overview_counts_kiosk_and_agent_orders_together(session: Session) -> None:
    user = session.get(User, "user_test")
    kiosk_order = create_order(session, user, _order_payload(OrderSource.kiosk_premium, quantity=1))
    agent_order = create_order(session, user, _order_payload(OrderSource.ai_agent, quantity=2))

    approve_dummy_payment(
        session,
        user,
        DummyPaymentApproveRequest(order_id=kiosk_order.id, idempotency_key="admin-kiosk-order"),
    )
    approve_dummy_payment(
        session,
        user,
        DummyPaymentApproveRequest(order_id=agent_order.id, idempotency_key="admin-agent-order"),
    )

    overview = get_admin_overview(session)
    source_stats = {stat.source: stat for stat in overview.source_stats}

    assert overview.total_order_count == 2
    assert overview.today_order_count == 2
    assert overview.total_dummy_sales_amount == 3600
    assert overview.today_dummy_sales_amount == 3600
    assert overview.receipt_issued_count == 2
    assert overview.earned_points_total == 36
    assert source_stats[OrderSource.kiosk_premium].order_count == 1
    assert source_stats[OrderSource.kiosk_premium].paid_order_count == 1
    assert source_stats[OrderSource.ai_agent].order_count == 1
    assert source_stats[OrderSource.ai_agent].paid_order_count == 1

    recent_orders = list_admin_orders(session)
    assert {order.source for order in recent_orders} == {OrderSource.kiosk_premium, OrderSource.ai_agent}
    assert all(order.payment is not None for order in recent_orders)
    assert all(order.receipt is not None for order in recent_orders)


def test_admin_order_detail_includes_payment_points_receipt_and_items(session: Session) -> None:
    user = session.get(User, "user_test")
    order = create_order(session, user, _order_payload(OrderSource.kiosk_premium, quantity=2))
    approve_dummy_payment(
        session,
        user,
        DummyPaymentApproveRequest(order_id=order.id, idempotency_key="admin-order-detail"),
    )

    detail = get_admin_order_detail(session, order.id)

    assert detail.id == order.id
    assert detail.items[0].name_snapshot == "Test Set"
    assert detail.items[0].line_total == 2400
    assert detail.payment is not None
    assert detail.payment.status == PaymentStatus.approved
    assert detail.earned_points == 24
    assert detail.point_ledger[0].amount == 24
    assert detail.receipt is not None
    assert detail.receipt.order_id == order.id


def test_require_admin_user_rejects_regular_user(session: Session) -> None:
    user = session.get(User, "user_test")

    with pytest.raises(HTTPException) as exc_info:
        require_admin_user(user)

    assert exc_info.value.status_code == 403
