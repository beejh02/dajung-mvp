from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import MenuItem


def list_menu_items(session: Session) -> list[MenuItem]:
    statement = select(MenuItem).order_by(MenuItem.category, MenuItem.name)
    return list(session.exec(statement).all())


def get_menu_item(session: Session, menu_item_id: str) -> MenuItem:
    menu_item = session.get(MenuItem, menu_item_id)
    if menu_item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found")
    return menu_item
