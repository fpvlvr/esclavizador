"""
User Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator
from uuid import UUID
from datetime import datetime

from app.domain.constants import UserRole
from app.core.security import validate_password_strength


class UserResponse(BaseModel):
    """
    User response schema (public data only).

    Used for API responses - does NOT include password hash.
    """

    id: UUID = Field(description="User unique identifier")
    email: EmailStr = Field(description="User email address")
    role: UserRole = Field(description="User role (boss or worker)")
    organization_id: UUID = Field(description="Organization ID")
    is_active: bool = Field(description="Account active status")
    created_at: datetime = Field(description="Account creation timestamp")

    model_config = ConfigDict(
        from_attributes=True,  # Pydantic v2 (was orm_mode in v1)
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "role": "worker",
                "organization_id": "123e4567-e89b-12d3-a456-426614174001",
                "is_active": True,
                "created_at": "2025-01-09T12:00:00Z"
            }
        }
    )


class UserCreate(BaseModel):
    """User creation schema - boss creates user in existing org."""

    email: EmailStr = Field(description="User email address")
    password: str = Field(
        min_length=8,
        max_length=128,
        description="User password (8-128 chars, uppercase, lowercase, digit, special char required)"
    )
    role: UserRole = Field(description="User role (boss or worker)")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Password strength validation."""
        is_valid, error_msg = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "role": "worker"
            }
        }
    )


class UserUpdate(BaseModel):
    """User update schema - all fields optional."""

    role: UserRole | None = Field(default=None, description="User role (boss or worker)")
    is_active: bool | None = Field(default=None, description="Account active status")
    password: str | None = Field(
        default=None,
        min_length=8,
        max_length=128,
        description="New password (8-128 chars, uppercase, lowercase, digit, special char required). Only bosses can update workers' passwords."
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str | None) -> str | None:
        """Password strength validation (only if password is provided)."""
        if v is None:
            return v
        is_valid, error_msg = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "role": "worker",
                "is_active": True,
                "password": "NewSecurePass123!"
            }
        }
    )


class UserList(BaseModel):
    """Paginated user list response."""

    items: list[UserResponse] = Field(description="List of users")
    total: int = Field(description="Total number of users matching filters")
    limit: int = Field(description="Maximum items per page")
    offset: int = Field(description="Number of items skipped")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "email": "worker@example.com",
                        "role": "worker",
                        "organization_id": "123e4567-e89b-12d3-a456-426614174001",
                        "is_active": True,
                        "created_at": "2025-01-09T12:00:00Z"
                    }
                ],
                "total": 1,
                "limit": 50,
                "offset": 0
            }
        }
    )


class ProjectInfo(BaseModel):
    """Project info for user stats."""

    id: UUID = Field(description="Project ID")
    name: str = Field(description="Project name")
    color: str = Field(description="Project color hex code")

    model_config = ConfigDict(from_attributes=True)


class UserStatsResponse(BaseModel):
    """User with aggregated stats (projects + time)."""

    id: UUID = Field(description="User unique identifier")
    email: EmailStr = Field(description="User email address")
    role: UserRole = Field(description="User role (boss or worker)")
    organization_id: UUID = Field(description="Organization ID")
    is_active: bool = Field(description="Account active status")
    created_at: datetime = Field(description="Account creation timestamp")
    total_time_seconds: int = Field(description="Total tracked time in seconds for date range")
    projects: list[ProjectInfo] = Field(description="Projects user has worked on in date range")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "worker@example.com",
                "role": "worker",
                "organization_id": "123e4567-e89b-12d3-a456-426614174001",
                "is_active": True,
                "created_at": "2025-01-09T12:00:00Z",
                "total_time_seconds": 513300,
                "projects": [
                    {"id": "123e4567-e89b-12d3-a456-426614174002", "name": "Website Redesign", "color": "#3b82f6"},
                    {"id": "123e4567-e89b-12d3-a456-426614174003", "name": "Mobile App", "color": "#f59e0b"}
                ]
            }
        }
    )


class UserStatsList(BaseModel):
    """Paginated user stats list response."""

    items: list[UserStatsResponse] = Field(description="List of users with stats")
    total: int = Field(description="Total number of users matching filters")
    limit: int = Field(description="Maximum items per page")
    offset: int = Field(description="Number of items skipped")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "email": "worker@example.com",
                        "role": "worker",
                        "organization_id": "123e4567-e89b-12d3-a456-426614174001",
                        "is_active": True,
                        "created_at": "2025-01-09T12:00:00Z",
                        "total_time_seconds": 513300,
                        "projects": [
                            {"id": "123e4567-e89b-12d3-a456-426614174002", "name": "Website Redesign", "color": "#3b82f6"}
                        ]
                    }
                ],
                "total": 1,
                "limit": 50,
                "offset": 0
            }
        }
    )
