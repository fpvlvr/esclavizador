"""Pydantic schemas for Tag entity."""

from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime


class TagCreate(BaseModel):
    """Schema for creating a new tag."""

    name: str = Field(
        min_length=1,
        max_length=100,
        description="Tag name (1-100 characters, will be trimmed)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Bug Fix"
            }
        }
    )


class TagUpdate(BaseModel):
    """Schema for updating an existing tag."""

    name: str = Field(
        min_length=1,
        max_length=100,
        description="Tag name (1-100 characters, will be trimmed)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Feature Development"
            }
        }
    )


class TagResponse(BaseModel):
    """Schema for tag response."""

    id: UUID = Field(description="Tag unique identifier")
    name: str = Field(description="Tag name")
    organization_id: UUID = Field(description="Organization ID")
    created_at: datetime = Field(description="Creation timestamp")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Bug Fix",
                "organization_id": "123e4567-e89b-12d3-a456-426614174001",
                "created_at": "2025-01-15T12:00:00Z"
            }
        }
    )


class TagList(BaseModel):
    """Schema for paginated tag list response."""

    items: list[TagResponse] = Field(description="List of tags")
    total: int = Field(description="Total number of tags")
    limit: int = Field(description="Maximum items per page")
    offset: int = Field(description="Number of items skipped")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Bug Fix",
                        "organization_id": "123e4567-e89b-12d3-a456-426614174001",
                        "created_at": "2025-01-15T12:00:00Z"
                    }
                ],
                "total": 1,
                "limit": 50,
                "offset": 0
            }
        }
    )
