import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.core.config import get_settings
from app.core.security import (
    create_jwt,
    hash_handoff_token,
    hash_password,
    utc_now,
    verify_password,
)
from app.models import AgentHandoffToken, User
from app.models.enums import UserRole
from app.schemas.auth import SignupRequest


def _auth_failed() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication failed",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def get_user_by_email(session: Session, email: str) -> User | None:
    return session.exec(select(User).where(User.email == email.lower())).first()


def create_user(session: Session, payload: SignupRequest) -> User:
    if get_user_by_email(session, payload.email) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    settings = get_settings()
    user = User(
        id=f"user_{secrets.token_urlsafe(12)}",
        email=payload.email.lower(),
        password_hash=hash_password(payload.password, settings),
        name=payload.name,
        phone=payload.phone,
        role=UserRole.user,
        points_balance=0,
        created_at=utc_now(),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def authenticate_user(session: Session, email: str, password: str) -> User:
    user = get_user_by_email(session, email)
    if user is None or not verify_password(password, user.password_hash):
        raise _auth_failed()
    return user


def issue_access_token(user: User, token_use: str = "access") -> tuple[str, int]:
    settings = get_settings()
    expire_minutes = (
        settings.agent_access_token_expire_minutes
        if token_use == "agent"
        else settings.access_token_expire_minutes
    )
    token, _ = create_jwt(
        subject=user.id,
        role=user.role.value,
        token_use=token_use,
        expires_delta=timedelta(minutes=expire_minutes),
        settings=settings,
    )
    return token, expire_minutes * 60


def create_agent_handoff_token(session: Session, user: User) -> tuple[str, AgentHandoffToken, int]:
    settings = get_settings()
    raw_token = secrets.token_urlsafe(32)
    expires_delta = timedelta(minutes=settings.handoff_token_expire_minutes)
    handoff_token = AgentHandoffToken(
        user_id=user.id,
        token_hash=hash_handoff_token(raw_token, settings),
        expires_at=utc_now() + expires_delta,
    )
    session.add(handoff_token)
    session.commit()
    session.refresh(handoff_token)
    return raw_token, handoff_token, int(expires_delta.total_seconds())


def exchange_agent_handoff_token(session: Session, raw_token: str) -> tuple[User, str, int]:
    settings = get_settings()
    token_hash = hash_handoff_token(raw_token, settings)
    handoff_token = session.exec(
        select(AgentHandoffToken).where(AgentHandoffToken.token_hash == token_hash)
    ).first()

    now = utc_now()
    if (
        handoff_token is None
        or handoff_token.used_at is not None
        or _as_utc(handoff_token.expires_at) <= now
    ):
        raise _auth_failed()

    user = session.get(User, handoff_token.user_id)
    if user is None:
        raise _auth_failed()

    handoff_token.used_at = now
    session.add(handoff_token)
    session.commit()
    session.refresh(user)
    access_token, expires_in = issue_access_token(user, token_use="agent")
    return user, access_token, expires_in
