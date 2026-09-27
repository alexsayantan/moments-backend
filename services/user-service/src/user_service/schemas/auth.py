from datetime import datetime
import uuid
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from common_auth import TokenResponse


class UserRegisterRequest(BaseModel):
    """Payload for registering a new user."""

    email: EmailStr = Field(description="Unique email address")
    username: str = Field(min_length=3, max_length=50, description="Unique username handle")
    password: str = Field(min_length=8, max_length=128, description="Plaintext password (minimum 8 characters)")
    first_name: str | None = Field(default=None, max_length=50, description="User first name")
    last_name: str | None = Field(default=None, max_length=50, description="User last name")


class UserLoginRequest(BaseModel):
    """Payload for user authentication."""

    email_or_username: str = Field(description="Email address or username")
    password: str = Field(description="Account password")


class RefreshTokenRequest(BaseModel):
    """Payload for refreshing an expired access token."""

    refresh_token: str = Field(description="Valid JWT refresh token")


class UserResponse(BaseModel):
    """Public user profile response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    username: str
    first_name: str | None = None
    last_name: str | None = None
    is_active: bool
    is_verified: bool
    role_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime


class AuthResponse(BaseModel):
    """Combined authentication response containing tokens and user profile."""

    tokens: TokenResponse
    user: UserResponse
