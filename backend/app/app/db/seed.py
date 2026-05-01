import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlmodel import Session, select

from app.core.config import get_settings
from app.core.security import hash_password
from app.models import MenuItem, User
from app.models.enums import UserRole


def _load_json(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as source:
        return json.load(source)


def _parse_datetime(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    return datetime.fromisoformat(value)


def _hash_seed_password(password: str) -> str:
    return hash_password(password, get_settings())


def _normalize_option_groups(option_groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized_groups: list[dict[str, Any]] = []
    for group in option_groups:
        normalized_groups.append(
            {
                "id": group["group_id"],
                "name": group["name"],
                "required": group["required"],
                "min_select": group["min_select"],
                "max_select": group["max_select"],
                "choices": [
                    {
                        "id": option["option_id"],
                        "name": option["name"],
                        "price_delta": option["price_delta"],
                        "is_available": option["is_available"],
                    }
                    for option in group.get("options", [])
                ],
            }
        )
    return normalized_groups


def _upsert_user(session: Session, payload: dict[str, Any]) -> None:
    user = session.get(User, payload["id"])
    if user is None:
        user = session.exec(select(User).where(User.email == payload["email"])).first()

    values = {
        "id": payload["id"],
        "email": payload["email"],
        "password_hash": _hash_seed_password(payload["password"]),
        "name": payload["name"],
        "phone": payload.get("phone"),
        "role": UserRole(payload["role"]),
        "points_balance": 0,
        "created_at": _parse_datetime(payload.get("created_at")),
    }

    if user is None:
        session.add(User(**values))
        return

    for key, value in values.items():
        setattr(user, key, value)
    session.add(user)


def _upsert_menu_item(session: Session, payload: dict[str, Any]) -> None:
    menu_item = session.get(MenuItem, payload["id"])
    values = {
        "id": payload["id"],
        "brand_id": payload.get("brand_id"),
        "name": payload["name"],
        "category": payload["category"],
        "description": payload.get("description"),
        "price": payload["base_price"],
        "image_url": payload.get("image_url"),
        "is_available": payload.get("is_available", True),
        "ingredients": payload.get("ingredients", []),
        "options": _normalize_option_groups(payload.get("option_groups", [])),
    }

    if menu_item is None:
        session.add(MenuItem(**values))
        return

    for key, value in values.items():
        setattr(menu_item, key, value)
    session.add(menu_item)


def seed_database(session: Session) -> dict[str, int]:
    settings = get_settings()
    users = _load_json(settings.seed_data_dir / "users.json")
    menu_items = _load_json(settings.seed_data_dir / "menus.json")

    for user in users:
        _upsert_user(session, user)

    for menu_item in menu_items:
        _upsert_menu_item(session, menu_item)

    session.commit()
    return {"users": len(users), "menu_items": len(menu_items)}
