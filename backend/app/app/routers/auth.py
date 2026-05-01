from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.dependencies import get_current_access_user, get_current_user
from app.db.session import get_session
from app.models import User
from app.schemas.auth import (
    AgentHandoffResponse,
    AgentSessionRequest,
    AgentSessionResponse,
    LoginRequest,
    SignupRequest,
    TokenResponse,
)
from app.schemas.user import UserRead
from app.services.auth_service import (
    authenticate_user,
    create_agent_handoff_token,
    create_user,
    exchange_agent_handoff_token,
    issue_access_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, session: Session = Depends(get_session)) -> TokenResponse:
    user = create_user(session, payload)
    access_token, expires_in = issue_access_token(user)
    return TokenResponse(access_token=access_token, expires_in=expires_in, user=UserRead.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, session: Session = Depends(get_session)) -> TokenResponse:
    user = authenticate_user(session, payload.email, payload.password)
    access_token, expires_in = issue_access_token(user)
    return TokenResponse(access_token=access_token, expires_in=expires_in, user=UserRead.model_validate(user))


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)


@router.post("/agent-handoff", response_model=AgentHandoffResponse)
def agent_handoff(
    current_user: User = Depends(get_current_access_user),
    session: Session = Depends(get_session),
) -> AgentHandoffResponse:
    raw_token, handoff_token, expires_in = create_agent_handoff_token(session, current_user)
    return AgentHandoffResponse(
        handoff_token=raw_token,
        expires_in=expires_in,
        expires_at=handoff_token.expires_at,
    )


@router.post("/agent-session", response_model=AgentSessionResponse)
def agent_session(payload: AgentSessionRequest, session: Session = Depends(get_session)) -> AgentSessionResponse:
    user, access_token, expires_in = exchange_agent_handoff_token(session, payload.handoff_token)
    return AgentSessionResponse(
        access_token=access_token,
        expires_in=expires_in,
        user=UserRead.model_validate(user),
    )
