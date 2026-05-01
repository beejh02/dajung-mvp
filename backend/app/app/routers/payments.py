from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.dependencies import get_current_user
from app.db.session import get_session
from app.models import User
from app.schemas.payment import DummyPaymentApproveRequest, PaymentRead
from app.services.payment_service import approve_dummy_payment, get_payment_for_user

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/dummy/approve", response_model=PaymentRead)
def approve_payment(
    payload: DummyPaymentApproveRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> PaymentRead:
    return PaymentRead.model_validate(approve_dummy_payment(session, current_user, payload))


@router.get("/{payment_id}", response_model=PaymentRead)
def get_payment(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> PaymentRead:
    return PaymentRead.model_validate(get_payment_for_user(session, payment_id, current_user))
