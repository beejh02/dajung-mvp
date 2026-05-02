from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.dependencies import get_current_user
from app.db.session import get_session
from app.models import User
from app.schemas.agent import (
    AgentMenuRead,
    AgentOrderConfirmRequest,
    AgentOrderDraftRead,
    AgentOrderDraftRequest,
    AgentPaymentApproveRead,
    AgentPaymentApproveRequest,
    AgentUserContextRead,
)
from app.schemas.order import OrderRead
from app.services.agent_service import (
    approve_agent_dummy_payment,
    confirm_agent_order,
    create_agent_order_draft,
    get_agent_menu,
    get_agent_user_context,
)

router = APIRouter(prefix="/agent", tags=["agent"])


@router.get("/menu", response_model=AgentMenuRead)
def list_agent_menu(
    _current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> AgentMenuRead:
    return get_agent_menu(session)


@router.get("/user-context", response_model=AgentUserContextRead)
def get_user_context(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> AgentUserContextRead:
    return get_agent_user_context(session, current_user)


@router.post("/orders/draft", response_model=AgentOrderDraftRead)
def create_order_draft(
    payload: AgentOrderDraftRequest,
    _current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> AgentOrderDraftRead:
    return create_agent_order_draft(session, payload)


@router.post("/orders/confirm", response_model=OrderRead)
def confirm_order(
    payload: AgentOrderConfirmRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> OrderRead:
    return confirm_agent_order(session, current_user, payload)


@router.post("/payments/dummy/approve", response_model=AgentPaymentApproveRead)
def approve_dummy_payment(
    payload: AgentPaymentApproveRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> AgentPaymentApproveRead:
    return approve_agent_dummy_payment(session, current_user, payload)
