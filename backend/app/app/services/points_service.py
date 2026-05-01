from sqlmodel import Session, select

from app.models import PointLedger, User


def calculate_earn_points(total_amount: int) -> int:
    return max(total_amount // 100, 0)


def list_point_ledger(session: Session, user: User) -> list[PointLedger]:
    statement = (
        select(PointLedger)
        .where(PointLedger.user_id == user.id)
        .order_by(PointLedger.created_at.desc(), PointLedger.id.desc())
    )
    return list(session.exec(statement).all())
