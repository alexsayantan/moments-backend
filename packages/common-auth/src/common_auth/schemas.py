from typing import Any
import uuid
from pydantic import BaseModel, Field


class UserClaims(BaseModel):
    """Claims extracted from a verified JWT access token."""

    sub: str = Field(description="Subject identifier (User UUID)")
    email: str
    username: str
    role: int = Field(description="Role integer (0=Banned, 1=Superadmin, 2=Platform Admin, 3=Admin, 5=Seller, 6=User)")
    permissions: dict[str, Any] = Field(default_factory=dict, description="JSONB permissions map")
    token_type: str = Field(default="access")
    exp: int | None = None
    iat: int | None = None
    iss: str | None = None
    aud: str | None = None

    @property
    def user_id(self) -> uuid.UUID:
        """Return the subject as a UUID object."""
        return uuid.UUID(self.sub)

    @property
    def is_banned(self) -> bool:
        """Check if user account is banned."""
        return self.role == 0

    @property
    def is_superadmin(self) -> bool:
        """Check if user is superadmin."""
        return self.role == 1

    def has_permission(self, domain: str, action: str) -> bool:
        """Check if claims grant permission for a specific domain action.

        Example: claims.has_permission("users", "create")
        Superadmins (role=1) or wildcard permissions '*' automatically pass.
        """
        if self.is_superadmin or "*" in self.permissions:
            return True
        domain_perms = self.permissions.get(domain)
        if not domain_perms:
            return False
        if isinstance(domain_perms, list):
            return action in domain_perms or "*" in domain_perms
        if isinstance(domain_perms, dict):
            return bool(domain_perms.get(action) or domain_perms.get("*"))
        return False


class TokenResponse(BaseModel):
    """Standard OAuth2 token response body."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
