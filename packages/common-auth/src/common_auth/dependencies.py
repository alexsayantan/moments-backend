from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from common_auth.jwt import verify_access_token
from common_auth.schemas import UserClaims

# HTTPBearer extracts Authorization: Bearer <token>
bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> UserClaims:
    """FastAPI dependency to extract and validate the JWT Bearer token.

    Returns the authenticated UserClaims, or raises 401 Unauthorized / 403 Forbidden.
    """
    token = credentials.credentials
    try:
        claims = verify_access_token(token)
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if claims.is_banned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been suspended or banned",
        )

    return claims


def require_role(*allowed_roles: int) -> Callable[..., UserClaims]:
    """Dependency factory restricting endpoints to specific numeric roles.

    Superadmins (role=1) automatically bypass this check.
    """

    async def role_checker(
        claims: UserClaims = Depends(get_current_user),
    ) -> UserClaims:
        if claims.is_superadmin:
            return claims
        if claims.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role privileges for this operation",
            )
        return claims

    return role_checker


def require_permission(domain: str, action: str) -> Callable[..., UserClaims]:
    """Dependency factory checking fine-grained JSONB permissions.

    Superadmins (role=1) automatically pass.
    """

    async def permission_checker(
        claims: UserClaims = Depends(get_current_user),
    ) -> UserClaims:
        if not claims.has_permission(domain, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: '{domain}.{action}'",
            )
        return claims

    return permission_checker
