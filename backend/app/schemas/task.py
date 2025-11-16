"""
Pydantic schemas for Task entity.

Defines request and response models for task-related API endpoints.
"""

from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime
from typing import Optional


class TaskCreate(BaseModel):
    """Schema for creating a new task."""

    name: str = Field(
        min_length=2,
        max_length=255,
        description="Task name (2-255 characters)"
    )
    description: Optional[str] = Field(
        default=None,
        description="Task description (optional)"
    )
    project_id: UUID = Field(
        description="Project ID this task belongs to"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Design mockups",
                "description": "Create initial design mockups in Figma",
                "project_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }
    )


class TaskUpdate(BaseModel):
    """Schema for updating an existing task."""

    name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=255,
        description="Task name (2-255 characters)"
    )
    description: Optional[str] = Field(
        default=None,
        description="Task description"
    )
    is_active: Optional[bool] = Field(
        default=None,
        description="Active status (soft delete)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Design mockups V2",
                "description": "Updated description",
                "is_active": True
            }
        }
    )


class TaskResponse(BaseModel):
    """Schema for task response (used for all endpoints)."""

    id: UUID = Field(description="Task unique identifier")
    name: str = Field(description="Task name")
    description: Optional[str] = Field(description="Task description")
    project_id: UUID = Field(description="Project ID")
    project_name: str = Field(description="Project name")
    is_active: bool = Field(description="Active status")
    created_at: datetime = Field(description="Creation timestamp")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174002",
                "name": "Design mockups",
                "description": "Create initial design mockups in Figma",
                "project_id": "123e4567-e89b-12d3-a456-426614174000",
                "project_name": "Website Redesign",
                "is_active": True,
                "created_at": "2025-01-15T12:00:00Z"
            }
        }
    )


class TaskList(BaseModel):
    """Schema for paginated task list response."""

    items: list[TaskResponse] = Field(description="List of tasks")
    total: int = Field(description="Total number of tasks matching filters")
    limit: int = Field(description="Maximum items per page")
    offset: int = Field(description="Number of items skipped")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174002",
                        "name": "Design mockups",
                        "description": "Create initial design mockups in Figma",
                        "project_id": "123e4567-e89b-12d3-a456-426614174000",
                        "project_name": "Website Redesign",
                        "is_active": True,
                        "created_at": "2025-01-15T12:00:00Z"
                    }
                ],
                "total": 1,
                "limit": 50,
                "offset": 0
            }
        }
    )
