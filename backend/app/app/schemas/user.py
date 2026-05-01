from datetime import datetime

from pydantic import BaseModel

from app.models.enums import UserRole


class UserRead(BaseModel):
    id: str
    email: str
    name: str
    phone: str | None = None
    role: UserRole
    points_balance: int
    created_at: datetime
