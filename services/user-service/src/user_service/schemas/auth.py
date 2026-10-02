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


class MessageResponse(BaseModel):
    """Standard message response for actions that do not return resource data."""

    message: str = Field(description="Status message")


class VerifyEmailRequest(BaseModel):
    """Payload for verifying user account through email OTP."""

    email: EmailStr = Field(description="Registered account email address")
    otp: str = Field(min_length=4, max_length=10, description="6-digit verification code sent to email")


class SendOtpRequest(BaseModel):
    """Payload to request an OTP for email verification."""

    email: EmailStr = Field(description="Registered account email address")


class ForgotPasswordRequest(BaseModel):
    """Payload to initiate password reset via email OTP."""

    email: EmailStr = Field(description="Registered account email address")


class ResetPasswordRequest(BaseModel):
    """Payload to reset account password using email OTP."""

    email: EmailStr = Field(description="Registered account email address")
    otp: str = Field(min_length=4, max_length=10, description="6-digit password reset code")
    new_password: str = Field(
        min_length=8,
        max_length=128,
        description="New plaintext password (minimum 8 characters)",
    )


class ResendOtpRequest(BaseModel):
    """Payload to resend an OTP for a specific purpose."""

    email: EmailStr = Field(description="Registered account email address")
    purpose: str = Field(
        default="email_verification",
        description="Purpose of OTP ('email_verification' or 'password_reset')",
    )
