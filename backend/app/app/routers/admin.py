from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.dependencies import require_admin_user
from app.db.session import get_session
from app.models import User
from app.schemas.admin import (
    AdminOrderDetailRead,
    AdminOrderSummaryRead,
    AdminOverviewRead,
    AdminPaymentStatusRead,
    AdminPointLedgerEntryRead,
    AdminReceiptStatusRead,
)
from app.services.admin_service import (
    get_admin_order_detail,
    get_admin_overview,
    list_admin_orders,
    list_admin_payments,
    list_admin_points,
    list_admin_receipts,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/overview", response_model=AdminOverviewRead)
def get_overview(
    _admin_user: User = Depends(require_admin_user),
    session: Session = Depends(get_session),
) -> AdminOverviewRead:
    return get_admin_overview(session)


@router.get("/orders", response_model=list[AdminOrderSummaryRead])
def get_orders(
    _admin_user: User = Depends(require_admin_user),
    session: Session = Depends(get_session),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[AdminOrderSummaryRead]:
    return list_admin_orders(session, limit=limit)


@router.get("/orders/{order_id}", response_model=AdminOrderDetailRead)
def get_order_detail(
    order_id: int,
    _admin_user: User = Depends(require_admin_user),
    session: Session = Depends(get_session),
) -> AdminOrderDetailRead:
    return get_admin_order_detail(session, order_id)


@router.get("/payments", response_model=list[AdminPaymentStatusRead])
def get_payments(
    _admin_user: User = Depends(require_admin_user),
    session: Session = Depends(get_session),
    limit: int = Query(default=100, ge=1, le=200),
) -> list[AdminPaymentStatusRead]:
    return list_admin_payments(session, limit=limit)


@router.get("/points", response_model=list[AdminPointLedgerEntryRead])
def get_points(
    _admin_user: User = Depends(require_admin_user),
    session: Session = Depends(get_session),
    limit: int = Query(default=100, ge=1, le=200),
) -> list[AdminPointLedgerEntryRead]:
    return list_admin_points(session, limit=limit)


@router.get("/receipts", response_model=list[AdminReceiptStatusRead])
def get_receipts(
    _admin_user: User = Depends(require_admin_user),
    session: Session = Depends(get_session),
    limit: int = Query(default=100, ge=1, le=200),
) -> list[AdminReceiptStatusRead]:
    return list_admin_receipts(session, limit=limit)
