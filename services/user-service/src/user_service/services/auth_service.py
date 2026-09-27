import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, or_
from sqlmodel import Session, select

from common_auth import (
    TokenResponse,
    auth_settings,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from user_service.core.security import hash_password, verify_password
from user_service.models import RoleEnum, User, UserRole
from user_service.schemas.auth import (
    AuthResponse,
    RefreshTokenRequest,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)


class AuthService:
    """Authentication service handling registration, password verification, and tokens."""

    @staticmethod
    def get_or_create_default_role(session: Session) -> UserRole:
        """Fetch the default USER role from the database or create it if missing."""
        statement = select(UserRole).where(UserRole.role == RoleEnum.USER)
        role = session.exec(statement).first()
        if not role:
            role = UserRole(
                role=RoleEnum.USER,
                name="User",
                description="Default standard user role",
                permissions={"users": ["read_self", "update_self"]},
            )
            session.add(role)
            session.commit()
            session.refresh(role)
        return role

    @classmethod
    def register(cls, session: Session, request: UserRegisterRequest) -> User:
        """Register a new user account with hashed password and default role."""
        # Check email uniqueness (case-insensitive)
        email_clean = request.email.lower().strip()
        existing_email = session.exec(
            select(User).where(func.lower(User.email) == email_clean)
        ).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email address already exists",
            )

        # Check username uniqueness
        existing_username = session.exec(
            select(User).where(User.username == request.username.strip())
        ).first()
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This username is already taken",
            )

        # Assign default role
        default_role = cls.get_or_create_default_role(session)

        # Create user with Argon2id hash
        new_user = User(
            email=email_clean,
            username=request.username.strip(),
            hashed_password=hash_password(request.password),
            first_name=request.first_name,
            last_name=request.last_name,
            role_id=default_role.id,
            is_active=True,
            is_verified=False,
        )

        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        return new_user

    @classmethod
    def authenticate(cls, session: Session, request: UserLoginRequest) -> User:
        """Authenticate user credentials by email or username."""
        identifier = request.email_or_username.strip()

        statement = select(User).where(
            or_(
                func.lower(User.email) == identifier.lower(),
                User.username == identifier,
            )
        )
        user = session.exec(statement).first()

        if not user or not verify_password(request.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email/username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated. Please contact support.",
            )

        if user.role and user.role.role == RoleEnum.BANNED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account has been suspended or banned.",
            )

        return user

    @classmethod
    def create_tokens(cls, user: User) -> TokenResponse:
        """Generate access and refresh tokens for an authenticated user."""
        role_value = int(user.role.role) if user.role else int(RoleEnum.USER)
        permissions = user.role.permissions if user.role else {}

        access_token = create_access_token(
            user_id=user.id,
            email=user.email,
            username=user.username,
            role=role_value,
            permissions=permissions,
        )
        refresh_token = create_refresh_token(user_id=user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=auth_settings.access_token_expire_minutes * 60,
        )

    @classmethod
    def refresh(cls, session: Session, request: RefreshTokenRequest) -> TokenResponse:
        """Validate a refresh token and return new tokens."""
        try:
            payload = decode_token(request.refresh_token, expected_token_type="refresh")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid or expired refresh token: {e}",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id = uuid.UUID(payload["sub"])
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated",
            )

        return cls.create_tokens(user)


auth_service = AuthService()
