import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.config import Settings


class TokenError(ValueError):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def hash_password(password: str, settings: Settings) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        settings.password_hash_iterations,
    )
    return "$".join(
        [
            "pbkdf2_sha256",
            str(settings.password_hash_iterations),
            _base64url_encode(salt),
            _base64url_encode(digest),
        ]
    )


def verify_password(password: str, password_hash: str) -> bool:
    if password_hash.startswith("seed-sha256:"):
        expected = password_hash.removeprefix("seed-sha256:")
        actual = hashlib.sha256(password.encode("utf-8")).hexdigest()
        return hmac.compare_digest(actual, expected)

    try:
        algorithm, iterations_text, salt_text, digest_text = password_hash.split("$", 3)
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    try:
        iterations = int(iterations_text)
        salt = _base64url_decode(salt_text)
        expected = _base64url_decode(digest_text)
    except (TypeError, ValueError):
        return False

    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual, expected)


def hash_handoff_token(token: str, settings: Settings) -> str:
    digest = hmac.new(
        settings.jwt_secret_key.encode("utf-8"),
        token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"hmac-sha256:{digest}"


def create_jwt(
    *,
    subject: str,
    role: str,
    token_use: str,
    expires_delta: timedelta,
    settings: Settings,
) -> tuple[str, datetime]:
    if settings.jwt_algorithm != "HS256":
        raise TokenError("unsupported jwt algorithm")

    issued_at = utc_now()
    expires_at = issued_at + expires_delta
    header = {"alg": settings.jwt_algorithm, "typ": "JWT"}
    payload = {
        "sub": subject,
        "role": role,
        "token_use": token_use,
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }

    signing_input = ".".join(
        [
            _base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8")),
            _base64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")),
        ]
    )
    signature = hmac.new(
        settings.jwt_secret_key.encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return f"{signing_input}.{_base64url_encode(signature)}", expires_at


def decode_jwt(token: str, settings: Settings) -> dict[str, Any]:
    if settings.jwt_algorithm != "HS256":
        raise TokenError("unsupported jwt algorithm")

    parts = token.split(".")
    if len(parts) != 3:
        raise TokenError("invalid token format")

    signing_input = ".".join(parts[:2])
    expected_signature = hmac.new(
        settings.jwt_secret_key.encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()

    try:
        provided_signature = _base64url_decode(parts[2])
    except (TypeError, ValueError) as exc:
        raise TokenError("invalid token signature") from exc

    if not hmac.compare_digest(provided_signature, expected_signature):
        raise TokenError("invalid token signature")

    try:
        header = json.loads(_base64url_decode(parts[0]))
        payload = json.loads(_base64url_decode(parts[1]))
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
        raise TokenError("invalid token payload") from exc

    if header.get("alg") != settings.jwt_algorithm:
        raise TokenError("invalid token algorithm")

    expires_at = payload.get("exp")
    if not isinstance(expires_at, int) or expires_at <= int(utc_now().timestamp()):
        raise TokenError("token expired")

    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise TokenError("invalid token subject")

    return payload
