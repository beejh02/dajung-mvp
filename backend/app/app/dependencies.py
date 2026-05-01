from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.core.config import get_settings
from app.core.security import TokenError, decode_jwt
from app.db.session import get_session
from app.models import User
from app.models.enums import UserRole

bearer_scheme = HTTPBearer(auto_error=False)


def _credentials_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _get_current_user_with_token_use(
    credentials: HTTPAuthorizationCredentials | None,
    session: Session,
    allowed_token_uses: set[str],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _credentials_error()

    try:
        payload = decode_jwt(credentials.credentials, get_settings())
    except TokenError as exc:
        raise _credentials_error() from exc

    token_use = payload.get("token_use")
    if token_use not in allowed_token_uses:
        raise _credentials_error()

    user = session.get(User, payload["sub"])
    if user is None:
        raise _credentials_error()

    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    session: Session = Depends(get_session),
) -> User:
    return _get_current_user_with_token_use(credentials, session, {"access", "agent"})


def get_current_access_user(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    session: Session = Depends(get_session),
) -> User:
    return _get_current_user_with_token_use(credentials, session, {"access"})


def require_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return current_user
