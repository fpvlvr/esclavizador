"""
User Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, Field, EmailStr, ConfigDict
from uuid import UUID
from datetime import datetime

from app.models.user import UserRole


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
