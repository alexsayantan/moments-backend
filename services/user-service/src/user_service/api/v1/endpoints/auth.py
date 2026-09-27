from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from common_auth import UserClaims, get_current_user
from user_service.db import get_session
from user_service.models import User
from user_service.schemas.auth import (
    AuthResponse,
    RefreshTokenRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from user_service.services.auth_service import auth_service

router = APIRouter()


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates a new user account with hashed password and returns access/refresh tokens.",
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


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user profile",
    description="Returns the profile of the user identified by the Bearer token.",
)
def get_me(
    claims: UserClaims = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> UserResponse:
    user = session.get(User, claims.user_id)
    return UserResponse.model_validate(user)
