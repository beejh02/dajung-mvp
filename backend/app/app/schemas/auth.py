from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.schemas.user import UserRead


class SignupRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=80)
    phone: str | None = Field(default=None, max_length=40)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        email = value.strip().lower()
        if "@" not in email or email.startswith("@") or email.endswith("@"):
            raise ValueError("valid email is required")
        return email


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    token_use: str = "access"
    user: UserRead


class AgentHandoffResponse(BaseModel):
    handoff_token: str
    token_type: str = "handoff"
    expires_in: int
    expires_at: datetime


class AgentSessionRequest(BaseModel):
    handoff_token: str = Field(min_length=16)


class AgentSessionResponse(TokenResponse):
    token_use: str = "agent"
