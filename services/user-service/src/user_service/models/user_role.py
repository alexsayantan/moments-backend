from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, Field, Relationship
from user_service.db.base import BaseAuditModel
from typing import TYPE_CHECKING, Any
from sqlalchemy import JSON
from enum import IntEnum


if TYPE_CHECKING:
    from user_service.models.user import User


class RoleEnum(IntEnum):
    """Enumeration of user roles and their associated privilege levels.

    Superadmin = 1
    Platform Admin = 2
    Admin = 3
    Seller = 5
    User = 6
    Banned = 0
    """

    BANNED = 0
    SUPERADMIN = 1
    PLATFORM_ADMIN = 2
    ADMIN = 3
    SELLER = 5
    USER = 6


class UserRole(BaseAuditModel, table=True):
    """User role and permissions table definition."""

    __tablename__ = "user_roles"

    role: RoleEnum = Field(
        unique=True,
        index=True,
        nullable=False,
        description="Role identifier (0=Banned, 1=Superadmin, 2=Platform Admin, 3=Admin, 5=Seller, 6=User)",
    )
    permissions: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(
            JSON().with_variant(JSONB, "postgresql"),
            nullable=False,
            server_default="{}",
        ),
        description="JSONB document storing specific permissions and scopes",
    )

    users: list["User"] = Relationship(back_populates="role")
