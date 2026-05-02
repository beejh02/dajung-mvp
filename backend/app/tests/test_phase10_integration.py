from datetime import timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.core.security import utc_now
from app.models import MenuItem, Payment, PointLedger, Receipt
from app.models.enums import OrderSource, OrderStatus
from app.schemas.agent import AgentOrderConfirmRequest, AgentPaymentApproveRequest
from app.schemas.auth import SignupRequest
from app.schemas.order import OrderCreateRequest
from app.schemas.payment import DummyPaymentApproveRequest
from app.services.agent_service import approve_agent_dummy_payment, confirm_agent_order
from app.services.auth_service import create_agent_handoff_token, create_user, exchange_agent_handoff_token
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
            MenuItem(
                id="menu_phase10_set",
                name="Phase 10 Set",
                category="set",
                price=7900,
                is_available=True,
                options=[],
            )
        )
        session.commit()
        yield session


def _signup_payload(email: str = "phase10@example.test") -> SignupRequest:
    return SignupRequest(
        email=email,
        password="Phase10-demo-001!",
        name="통합 검증 사용자",
        phone="000-0000-1910",
    )


def _order_payload(source: OrderSource) -> OrderCreateRequest:
    return OrderCreateRequest.model_validate(
        {
            "source": source,
            "items": [{"menu_item_id": "menu_phase10_set", "quantity": 1, "selected_options": []}],
        }
    )


def test_signup_handoff_token_reuse_and_expiration(session: Session) -> None:
    user = create_user(session, _signup_payload())

    raw_token, handoff_token, _expires_in = create_agent_handoff_token(session, user)
    exchanged_user, access_token, expires_in = exchange_agent_handoff_token(session, raw_token)

    assert exchanged_user.id == user.id
    assert access_token
    assert expires_in > 0
    session.refresh(handoff_token)
    assert handoff_token.used_at is not None

    with pytest.raises(HTTPException) as reuse_exc:
        exchange_agent_handoff_token(session, raw_token)
    assert reuse_exc.value.status_code == 401

    expired_raw_token, expired_token, _expires_in = create_agent_handoff_token(session, user)
    expired_token.expires_at = utc_now() - timedelta(seconds=1)
    session.add(expired_token)
    session.commit()

    with pytest.raises(HTTPException) as expired_exc:
        exchange_agent_handoff_token(session, expired_raw_token)
    assert expired_exc.value.status_code == 401


def test_kiosk_and_agent_orders_share_payment_points_receipt_pipeline(session: Session) -> None:
    user = create_user(session, _signup_payload("phase10.pipeline@example.test"))

    kiosk_order = create_order(session, user, _order_payload(OrderSource.kiosk_premium))
    kiosk_payment = approve_dummy_payment(
        session,
        user,
        DummyPaymentApproveRequest(order_id=kiosk_order.id, idempotency_key="phase10-kiosk-once"),
    )
    kiosk_payment_retry = approve_dummy_payment(
        session,
        user,
        DummyPaymentApproveRequest(order_id=kiosk_order.id, idempotency_key="phase10-kiosk-once"),
    )

    agent_order = confirm_agent_order(
        session,
        user,
        AgentOrderConfirmRequest.model_validate(
            {"items": [{"menu_item_id": "menu_phase10_set", "quantity": 1, "selected_options": []}]}
        ),
    )
    agent_payment = approve_agent_dummy_payment(
        session,
        user,
        AgentPaymentApproveRequest(order_id=agent_order.id, idempotency_key="phase10-agent-once"),
    )

    session.refresh(user)
    session.refresh(kiosk_order)

    assert kiosk_payment.id == kiosk_payment_retry.id
    assert kiosk_order.status == OrderStatus.paid
    assert agent_order.source == OrderSource.ai_agent
    assert agent_payment.payment.order_id == agent_order.id
    assert user.points_balance == 158
    assert len(session.exec(select(Payment)).all()) == 2
    assert len(session.exec(select(PointLedger)).all()) == 2
    assert len(session.exec(select(Receipt)).all()) == 2
