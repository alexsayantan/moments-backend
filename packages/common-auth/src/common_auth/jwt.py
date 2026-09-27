from datetime import datetime, timedelta, timezone
from typing import Any
import uuid

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from common_auth.config import AuthSettings, auth_settings
from common_auth.schemas import UserClaims


def _get_signing_key(settings: AuthSettings) -> str:
    """Return private key for asymmetric algorithms (RS256/EdDSA) or secret key for symmetric."""
    if settings.jwt_algorithm.startswith("RS") or settings.jwt_algorithm.startswith("ES"):
        if not settings.jwt_private_key:
            raise ValueError(f"jwt_private_key must be configured for algorithm {settings.jwt_algorithm}")
        return settings.jwt_private_key
    return settings.jwt_secret_key


def _get_verification_key(settings: AuthSettings) -> str:
    """Return public key for asymmetric algorithms or secret key for symmetric."""
    if settings.jwt_algorithm.startswith("RS") or settings.jwt_algorithm.startswith("ES"):
        if not settings.jwt_public_key:
            raise ValueError(f"jwt_public_key must be configured for algorithm {settings.jwt_algorithm}")
        return settings.jwt_public_key
    return settings.jwt_secret_key


def create_access_token(
    user_id: uuid.UUID | str,
    email: str,
    username: str,
    role: int,
    permissions: dict[str, Any] | None = None,
    expires_delta: timedelta | None = None,
    custom_claims: dict[str, Any] | None = None,
    settings: AuthSettings = auth_settings,
) -> str:
    """Create a signed JWT access token containing standard UserClaims."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.access_token_expire_minutes)

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "email": email,
        "username": username,
        "role": int(role),
        "permissions": permissions or {},
        "token_type": "access",
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "iss": settings.token_issuer,
        "aud": settings.token_audience,
    }

    if custom_claims:
        payload.update(custom_claims)

    key = _get_signing_key(settings)
    return jwt.encode(payload, key, algorithm=settings.jwt_algorithm)


def create_refresh_token(
    user_id: uuid.UUID | str,
    expires_delta: timedelta | None = None,
    settings: AuthSettings = auth_settings,
) -> str:
    """Create a signed JWT refresh token for renewing access tokens."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.refresh_token_expire_days)

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "token_type": "refresh",
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "iss": settings.token_issuer,
        "aud": settings.token_audience,
    }

    key = _get_signing_key(settings)
    return jwt.encode(payload, key, algorithm=settings.jwt_algorithm)


def decode_token(
    token: str,
    verify_exp: bool = True,
    expected_token_type: str | None = None,
    settings: AuthSettings = auth_settings,
) -> dict[str, Any]:
    """Decode and verify a JWT signature and standard claims."""
    key = _get_verification_key(settings)
    options = {"verify_exp": verify_exp, "verify_aud": bool(settings.token_audience)}

    payload: dict[str, Any] = jwt.decode(
        token,
        key,
        algorithms=[settings.jwt_algorithm],
        audience=settings.token_audience,
        issuer=settings.token_issuer,
        options=options,
    )

    if expected_token_type:
        actual_type = payload.get("token_type")
        if actual_type != expected_token_type:
            raise InvalidTokenError(f"Invalid token type: expected {expected_token_type}, got {actual_type}")

    return payload


def verify_access_token(
    token: str,
    settings: AuthSettings = auth_settings,
) -> UserClaims:
    """Decode and validate an access token, returning a validated UserClaims model."""
    payload = decode_token(token, verify_exp=True, expected_token_type="access", settings=settings)
    return UserClaims.model_validate(payload)
