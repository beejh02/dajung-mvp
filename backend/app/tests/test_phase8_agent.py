import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.models import MenuItem, Order, Payment, PointLedger, Receipt, User
from app.models.enums import OrderSource, PaymentStatus, UserRole
from app.schemas.agent import AgentOrderConfirmRequest, AgentOrderDraftRequest, AgentPaymentApproveRequest
from app.schemas.order import OrderCreateItem
from app.services.agent_service import (
    approve_agent_dummy_payment,
    confirm_agent_order,
    create_agent_order_draft,
    get_agent_menu,
    get_agent_user_context,
)


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
            MenuItem(
                id="menu_test_set",
                name="Test Set",
                category="set",
                price=1500,
                is_available=True,
                options=[],
            )
        )
        session.commit()
        yield session


def _agent_items(quantity: int = 1) -> list[OrderCreateItem]:
    return [
        OrderCreateItem.model_validate(
            {
                "menu_item_id": "menu_test_set",
                "quantity": quantity,
                "selected_options": [],
            }
        )
    ]


def test_agent_order_draft_prices_without_persisting_order(session: Session) -> None:
    draft = create_agent_order_draft(session, AgentOrderDraftRequest(items=_agent_items(quantity=2)))

    assert draft.source == OrderSource.ai_agent
    assert draft.total_amount == 3000
    assert draft.items[0].line_total == 3000
    assert session.exec(select(Order)).all() == []


def test_agent_confirm_and_payment_reuse_existing_pipeline(session: Session) -> None:
    user = session.get(User, "user_test")
    order = confirm_agent_order(session, user, AgentOrderConfirmRequest(items=_agent_items(quantity=1)))

    payment_result = approve_agent_dummy_payment(
        session,
        user,
        AgentPaymentApproveRequest(order_id=order.id, idempotency_key="agent-payment-once"),
    )

    assert order.source == OrderSource.ai_agent
    assert payment_result.payment.status == PaymentStatus.approved
    assert payment_result.receipt is not None
    assert payment_result.points.points_balance == 15
    assert len(session.exec(select(Payment)).all()) == 1
    assert len(session.exec(select(PointLedger)).all()) == 1
    assert len(session.exec(select(Receipt)).all()) == 1


def test_agent_menu_and_user_context_are_backend_reads(session: Session) -> None:
    user = session.get(User, "user_test")

    menu = get_agent_menu(session)
    context = get_agent_user_context(session, user)

    assert menu.items[0].id == "menu_test_set"
    assert context.user.id == "user_test"
    assert context.points.points_balance == 0
