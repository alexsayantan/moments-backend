from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from user_service.db import get_session
from user_service.schemas.auth import (
    AuthResponse,
    ForgotPasswordRequest,
    MessageResponse,
    RefreshTokenRequest,
    ResendOtpRequest,
    ResetPasswordRequest,
    SendOtpRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
    VerifyEmailRequest,
)
from user_service.services.auth_service import auth_service

router = APIRouter()


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates a new user account with hashed password, dispatches verification OTP to email, and returns initial tokens.",
)
def register(
    request: UserRegisterRequest,
    session: Session = Depends(get_session),
) -> AuthResponse:
    user = auth_service.register(session, request)
    tokens = auth_service.create_tokens(user)
    return AuthResponse(
        tokens=tokens,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and retrieve tokens",
    description="Validates credentials by email or username and issues access and refresh tokens.",
)
def login(
    request: UserLoginRequest,
    session: Session = Depends(get_session),
) -> AuthResponse:
    user = auth_service.authenticate(session, request)
    tokens = auth_service.create_tokens(user)
    return AuthResponse(
        tokens=tokens,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Issues a fresh pair of access and refresh tokens using a valid refresh token.",
)
def refresh_token(
    request: RefreshTokenRequest,
    session: Session = Depends(get_session),
) -> TokenResponse:
    return auth_service.refresh(session, request)


@router.post(
    "/verify-email",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify account email with OTP",
    description="Validates the email verification OTP stored in Redis and marks account as verified.",
)
def verify_email(
    request: VerifyEmailRequest,
    session: Session = Depends(get_session),
) -> MessageResponse:
    auth_service.verify_email(session, request.email, request.otp)
    return MessageResponse(message="Email verified successfully. Your account is now active.")


@router.post(
    "/send-verification-otp",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Send email verification OTP",
    description="Dispatches a 6-digit verification code to the user's email address with a 5-minute TTL.",
)
def send_verification_otp(
    request: SendOtpRequest,
    session: Session = Depends(get_session),
) -> MessageResponse:
    auth_service.send_verification_otp(session, request.email)
    return MessageResponse(message="Verification OTP sent to your email address.")


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Request password reset OTP",
    description="Generates a password reset code and delivers it to the user's registered email with TTL.",
)
def forgot_password(
    request: ForgotPasswordRequest,
    session: Session = Depends(get_session),
) -> MessageResponse:
    auth_service.request_password_reset(session, request.email)
    return MessageResponse(
        message="If an account with this email exists, a password reset code has been sent."
    )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset password with OTP",
    description="Validates the password reset OTP stored in Redis and updates the user's password.",
)
def reset_password(
    request: ResetPasswordRequest,
    session: Session = Depends(get_session),
) -> MessageResponse:
    auth_service.reset_password(session, request.email, request.otp, request.new_password)
    return MessageResponse(
        message="Password reset successfully. You can now log in with your new password."
    )


@router.post(
    "/resend-otp",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Resend verification or reset OTP",
    description="Regenerates and resends an OTP for email_verification or password_reset subject to cooldown.",
)
def resend_otp(
    request: ResendOtpRequest,
    session: Session = Depends(get_session),
) -> MessageResponse:
    auth_service.resend_otp(session, request.email, request.purpose)
    return MessageResponse(message="A new OTP has been dispatched to your email address.")
