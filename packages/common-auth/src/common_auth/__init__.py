from common_auth.config import AuthSettings, auth_settings
from common_auth.dependencies import (
    get_current_user,
    require_permission,
    require_role,
)
from common_auth.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_access_token,
)
from common_auth.schemas import TokenResponse, UserClaims

__all__ = [
    "AuthSettings",
    "auth_settings",
    "UserClaims",
    "TokenResponse",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "verify_access_token",
    "get_current_user",
    "require_role",
    "require_permission",
]
