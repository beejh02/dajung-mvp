from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.menu import MenuItemRead
from app.services.menu_service import get_menu_item, list_menu_items

router = APIRouter(prefix="/menu", tags=["menu"])


@router.get("", response_model=list[MenuItemRead])
def list_menu(session: Session = Depends(get_session)) -> list[MenuItemRead]:
    return [MenuItemRead.model_validate(menu_item) for menu_item in list_menu_items(session)]


@router.get("/{menu_item_id}", response_model=MenuItemRead)
def get_menu(menu_item_id: str, session: Session = Depends(get_session)) -> MenuItemRead:
    return MenuItemRead.model_validate(get_menu_item(session, menu_item_id))
