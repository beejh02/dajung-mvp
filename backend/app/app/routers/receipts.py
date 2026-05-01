from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.dependencies import get_current_user
from app.db.session import get_session
from app.models import User
from app.schemas.receipt import ReceiptRead
from app.services.receipt_service import get_order_receipt_for_user, get_receipt_for_user

router = APIRouter(tags=["receipts"])


@router.get("/receipts/{receipt_id}", response_model=ReceiptRead)
def get_receipt(
    receipt_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> ReceiptRead:
    return ReceiptRead.model_validate(get_receipt_for_user(session, receipt_id, current_user))


@router.get("/orders/{order_id}/receipt", response_model=ReceiptRead)
def get_order_receipt(
    order_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> ReceiptRead:
    return ReceiptRead.model_validate(get_order_receipt_for_user(session, order_id, current_user))
