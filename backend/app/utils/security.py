"""
JWT token creation and verification utilities.
Uses python-jose for JWT operations and passlib/bcrypt for password hashing.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Any
from uuid import UUID

from jose import jwt, JWTError

from app.config.settings import get_settings
from app.config.logging import get_logger

logger = get_logger("utils.security")


def create_access_token(
    subject: str | UUID,
    user_type: str,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Create a short-lived JWT access token."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)

    claims = {
        "sub": str(subject),
        "user_type": user_type,
        "type": "access",
        "iat": now,
        "exp": expire,
    }
    if extra_claims:
        claims.update(extra_claims)

    return jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(
    subject: str | UUID,
) -> str:
    """Create a long-lived JWT refresh token."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.refresh_token_expire_days)

    claims = {
        "sub": str(subject),
        "type": "refresh",
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any] | None:
    """
    Decode and verify a JWT token.
    Returns the payload dict on success, None if the token is invalid/expired.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        return None


def verify_access_token(token: str) -> dict[str, Any] | None:
    """Decode token and ensure it is an access token."""
    payload = decode_token(token)
    if payload is None:
        return None
    if payload.get("type") != "access":
        logger.warning("Token is not an access token")
        return None
    return payload


def verify_refresh_token(token: str) -> dict[str, Any] | None:
    """Decode token and ensure it is a refresh token."""
    payload = decode_token(token)
    if payload is None:
        return None
    if payload.get("type") != "refresh":
        logger.warning("Token is not a refresh token")
        return None
    return payload
