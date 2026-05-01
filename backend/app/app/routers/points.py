from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.dependencies import get_current_user
from app.db.session import get_session
from app.models import User
from app.schemas.points import PointBalanceRead, PointLedgerRead
from app.services.points_service import list_point_ledger

router = APIRouter(prefix="/points", tags=["points"])


@router.get("/me", response_model=PointBalanceRead)
def get_my_points(current_user: User = Depends(get_current_user)) -> PointBalanceRead:
    return PointBalanceRead(user_id=current_user.id, points_balance=current_user.points_balance)


@router.get("/ledger", response_model=list[PointLedgerRead])
def get_my_point_ledger(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[PointLedgerRead]:
    return [PointLedgerRead.model_validate(item) for item in list_point_ledger(session, current_user)]
