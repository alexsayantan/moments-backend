from user_service.db.base import BaseAuditModel
from typing import TYPE_CHECKING, Optional
from sqlmodel import Field, Relationship
import uuid


if TYPE_CHECKING:
    from user_service.models.user_role import UserRole


class User(BaseAuditModel, table=True):
    """User database table definition."""

    __tablename__ = "users"

    email: str = Field(
        unique=True,
        index=True,
        nullable=False,
        max_length=255,
        description="User email address (unique)",
    )
    username: str = Field(
        unique=True,
        index=True,
        nullable=False,
        max_length=50,
        description="Unique username handle",
    )
    hashed_password: str = Field(
        nullable=False,
        description="Argon2/bcrypt hashed user password",
    )
    first_name: str | None = Field(
        default=None,
        max_length=50,
        description="User first name",
    )
    last_name: str | None = Field(
        default=None,
        max_length=50,
        description="User last name",
    )
    is_active: bool = Field(
        default=True,
        nullable=False,
        description="Whether the user account is active",
    )
    is_verified: bool = Field(
        default=False,
        nullable=False,
        description="Whether the user email is verified",
    )
    role_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="user_roles.id",
        index=True,
        description="Foreign key referencing user_roles.id",
    )

    role: Optional["UserRole"] = Relationship(back_populates="users")
