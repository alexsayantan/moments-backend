from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from common_auth import UserClaims, get_current_user
from user_service.db import get_session
from user_service.models import User
from user_service.schemas.auth import UserResponse

router = APIRouter()


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user profile",
    description="Returns the profile of the user identified by the Bearer access token.",
)
def get_me(
    claims: UserClaims = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> UserResponse:
    user = session.get(User, claims.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserResponse.model_validate(user)
