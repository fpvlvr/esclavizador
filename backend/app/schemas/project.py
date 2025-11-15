"""
Pydantic schemas for Project entity.

Defines request and response models for project-related API endpoints.
"""

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional


class ProjectCreate(BaseModel):
    """Schema for creating a new project."""

    name: str = Field(
        min_length=2,
        max_length=255,
        description="Project name (2-255 characters)"
    )
    description: Optional[str] = Field(
        default=None,
        description="Project description (optional)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Website Redesign",
                "description": "Complete redesign of company website"
            }
        }


class ProjectUpdate(BaseModel):
    """Schema for updating an existing project."""

    name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=255,
        description="Project name (2-255 characters)"
    )
    description: Optional[str] = Field(
        default=None,
        description="Project description"
    )
    is_active: Optional[bool] = Field(
        default=None,
        description="Active status (soft delete)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Website Redesign V2",
                "description": "Updated description",
                "is_active": True
            }
        }


class ProjectResponse(BaseModel):
    """Schema for project response (used for all endpoints)."""

    id: UUID = Field(description="Project unique identifier")
    name: str = Field(description="Project name")
    description: Optional[str] = Field(description="Project description")
    organization_id: UUID = Field(description="Organization ID")
    is_active: bool = Field(description="Active status")
    created_at: datetime = Field(description="Creation timestamp")
    task_count: int = Field(
        default=0,
        description="Number of tasks in this project"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Website Redesign",
                "description": "Complete redesign of company website",
                "organization_id": "123e4567-e89b-12d3-a456-426614174001",
                "is_active": True,
                "created_at": "2025-01-15T12:00:00Z",
                "task_count": 5
            }
        }


class ProjectList(BaseModel):
    """Schema for paginated project list response."""

    items: list[ProjectResponse] = Field(description="List of projects")
    total: int = Field(description="Total number of projects matching filters")
    limit: int = Field(description="Maximum items per page")
    offset: int = Field(description="Number of items skipped")

    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Website Redesign",
                        "description": "Complete redesign of company website",
                        "organization_id": "123e4567-e89b-12d3-a456-426614174001",
                        "is_active": True,
                        "created_at": "2025-01-15T12:00:00Z",
                        "task_count": 5
                    }
                ],
                "total": 1,
                "limit": 50,
                "offset": 0
            }
        }
