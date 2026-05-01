import pytest
from fastapi import HTTPException
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.models import MenuItem, Order, Payment, PointLedger, Receipt, User
from app.models.enums import OrderSource, OrderStatus, UserRole
from app.schemas.order import OrderCreateRequest
from app.schemas.payment import DummyPaymentApproveRequest
from app.services.order_service import create_order, price_order, transition_order_status
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
                price=1000,
                is_available=True,
                options=[
                    {
                        "id": "drink",
                        "name": "Drink",
                        "required": True,
                        "min_select": 1,
                        "max_select": 1,
                        "choices": [
                            {"id": "cola", "name": "Cola", "price_delta": 0, "is_available": True},
                            {"id": "tea", "name": "Tea", "price_delta": 300, "is_available": True},
                        ],
                    },
                    {
                        "id": "add",
                        "name": "Add",
                        "required": False,
                        "min_select": 0,
                        "max_select": 2,
                        "choices": [
                            {"id": "cheese", "name": "Cheese", "price_delta": 500, "is_available": True},
                            {"id": "patty", "name": "Patty", "price_delta": 1500, "is_available": True},
                            {"id": "bacon", "name": "Bacon", "price_delta": 700, "is_available": False},
                        ],
                    },
                ],
            )
        )
        session.add(
            MenuItem(
                id="menu_inactive",
                name="Inactive",
                category="burger",
                price=1000,
                is_available=False,
                options=[],
            )
        )
        session.commit()
        yield session


def _valid_payload(quantity: int = 1) -> OrderCreateRequest:
    return OrderCreateRequest.model_validate(
        {
            "source": OrderSource.kiosk_premium,
            "client_total_amount": 1,
            "items": [
                {
                    "menu_item_id": "menu_test_set",
                    "quantity": quantity,
                    "selected_options": [
                        {"group_id": "drink", "choice_ids": ["cola"]},
                        {"group_id": "add", "choice_ids": ["cheese"]},
                    ],
                }
            ],
        }
    )


def test_price_order_recalculates_from_server_menu(session: Session) -> None:
    priced_order = price_order(session, _valid_payload(quantity=2))

    assert priced_order.items[0].unit_price == 1500
    assert priced_order.items[0].line_total == 3000
    assert priced_order.total_amount == 3000


@pytest.mark.parametrize(
    "payload",
    [
        {
            "source": OrderSource.kiosk_premium,
            "items": [{"menu_item_id": "menu_test_set", "quantity": 1, "selected_options": []}],
        },
        {
            "source": OrderSource.kiosk_premium,
            "items": [
                {
                    "menu_item_id": "menu_test_set",
                    "quantity": 1,
                    "selected_options": [
                        {"group_id": "drink", "choice_ids": ["cola"]},
                        {"group_id": "add", "choice_ids": ["cheese", "patty", "bacon"]},
                    ],
                }
            ],
        },
        {
            "source": OrderSource.kiosk_premium,
            "items": [
                {
                    "menu_item_id": "menu_test_set",
                    "quantity": 1,
                    "selected_options": [
                        {"group_id": "drink", "choice_ids": ["cola"]},
                        {"group_id": "add", "choice_ids": ["bacon"]},
                    ],
                }
            ],
        },
        {
            "source": OrderSource.kiosk_premium,
            "items": [{"menu_item_id": "menu_inactive", "quantity": 1, "selected_options": []}],
        },
    ],
)
def test_price_order_rejects_invalid_options(session: Session, payload: dict) -> None:
    with pytest.raises(HTTPException) as exc_info:
        price_order(session, OrderCreateRequest.model_validate(payload))

    assert exc_info.value.status_code == 400


def test_order_status_transition_allows_only_defined_paths(session: Session) -> None:
    order = Order(
        user_id="user_test",
        source=OrderSource.kiosk_premium,
        status=OrderStatus.pending_payment,
        total_amount=1500,
    )
    session.add(order)
    session.commit()
    session.refresh(order)

    paid_order = transition_order_status(session, order, OrderStatus.paid)
    assert paid_order.status == OrderStatus.paid

    with pytest.raises(HTTPException) as exc_info:
        transition_order_status(session, paid_order, OrderStatus.pending_payment)

    assert exc_info.value.status_code == 409


def test_dummy_order_failure_case_is_defined(session: Session) -> None:
    payload = OrderCreateRequest.model_validate(
        {
            "source": OrderSource.kiosk_premium,
            "simulate_failure": True,
            "items": [
                {
                    "menu_item_id": "menu_test_set",
                    "quantity": 1,
                    "selected_options": [{"group_id": "drink", "choice_ids": ["cola"]}],
                }
            ],
        }
    )

    with pytest.raises(HTTPException) as exc_info:
        price_order(session, payload)

    assert exc_info.value.status_code == 400


def test_dummy_payment_approval_is_idempotent(session: Session) -> None:
    user = session.get(User, "user_test")
    order = create_order(session, user, _valid_payload(quantity=1))
    request = DummyPaymentApproveRequest(order_id=order.id, idempotency_key="pay-once")

    first_payment = approve_dummy_payment(session, user, request)
    second_payment = approve_dummy_payment(session, user, request)
    session.refresh(user)

    assert first_payment.id == second_payment.id
    assert session.exec(select(Payment)).all() == [first_payment]
    assert len(session.exec(select(PointLedger)).all()) == 1
    assert len(session.exec(select(Receipt)).all()) == 1
    assert user.points_balance == 15


def test_dummy_payment_failure_case_skips_points_and_receipt(session: Session) -> None:
    user = session.get(User, "user_test")
    order = create_order(session, user, _valid_payload(quantity=1))

    payment = approve_dummy_payment(
        session,
        user,
        DummyPaymentApproveRequest(order_id=order.id, idempotency_key="fail-once", simulate_failure=True),
    )
    session.refresh(order)
    session.refresh(user)

    assert payment.status.value == "failed"
    assert order.status == OrderStatus.failed
    assert user.points_balance == 0
    assert len(session.exec(select(PointLedger)).all()) == 0
    assert len(session.exec(select(Receipt)).all()) == 0


def test_admin_payment_approval_credits_order_owner(session: Session) -> None:
    user = session.get(User, "user_test")
    admin = session.get(User, "admin_test")
    order = create_order(session, user, _valid_payload(quantity=1))

    approve_dummy_payment(
        session,
        admin,
        DummyPaymentApproveRequest(order_id=order.id, idempotency_key="admin-approve"),
    )
    session.refresh(user)
    session.refresh(admin)

    ledger = session.exec(select(PointLedger)).one()
    assert ledger.user_id == user.id
    assert user.points_balance == 15
    assert admin.points_balance == 0
