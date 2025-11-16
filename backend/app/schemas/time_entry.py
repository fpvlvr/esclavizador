"""
Pydantic schemas for time entry API requests and responses.

These schemas handle validation and serialization for the API layer.
"""

from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional


class TimeEntryStart(BaseModel):
    """Schema for starting a timer."""

    project_id: UUID = Field(..., description="Project to track time for")
    task_id: Optional[UUID] = Field(None, description="Optional task within project")
    is_billable: bool = Field(True, description="Whether time is billable")
    description: Optional[str] = Field(None, max_length=1000, description="Entry description")


class TimeEntryCreate(BaseModel):
    """Schema for creating a manual time entry."""

    project_id: UUID = Field(..., description="Project to track time for")
    task_id: Optional[UUID] = Field(None, description="Optional task within project")
    start_time: datetime = Field(..., description="Entry start time")
    end_time: datetime = Field(..., description="Entry end time")
    is_billable: bool = Field(True, description="Whether time is billable")
    description: Optional[str] = Field(None, max_length=1000, description="Entry description")

    @field_validator('end_time')
    @classmethod
    def end_after_start(cls, v: datetime, info) -> datetime:
        """Validate that end_time is after start_time."""
        if 'start_time' in info.data and v <= info.data['start_time']:
            raise ValueError('end_time must be after start_time')
        return v

    @field_validator('start_time', 'end_time')
    @classmethod
    def not_in_future(cls, v: datetime) -> datetime:
        """Validate that times are not in the future."""
        if v > datetime.utcnow():
            raise ValueError('Time cannot be in the future')
        return v


class TimeEntryUpdate(BaseModel):
    """Schema for updating a time entry (all fields optional)."""

    project_id: Optional[UUID] = Field(None, description="Project to track time for")
    task_id: Optional[UUID] = Field(None, description="Optional task within project")
    start_time: Optional[datetime] = Field(None, description="Entry start time")
    end_time: Optional[datetime] = Field(None, description="Entry end time")
    is_billable: Optional[bool] = Field(None, description="Whether time is billable")
    description: Optional[str] = Field(None, max_length=1000, description="Entry description")


class TimeEntryResponse(BaseModel):
    """Schema for time entry response."""

    id: UUID
    user_id: UUID
    user_email: str = Field(..., description="Email of user who created entry")
    project_id: UUID
    project_name: str = Field(..., description="Name of project")
    task_id: Optional[UUID]
    task_name: Optional[str] = Field(None, description="Name of task (if any)")
    organization_id: UUID
    start_time: datetime
    end_time: Optional[datetime]
    is_running: bool = Field(..., description="Whether timer is currently running")
    is_billable: bool
    description: Optional[str]
    duration_seconds: Optional[int] = Field(None, description="Duration in seconds (null for running timers)")
    created_at: datetime

    class Config:
        from_attributes = True


class TimeEntryList(BaseModel):
    """Schema for paginated time entry list."""

    items: list[TimeEntryResponse]
    total: int = Field(..., description="Total number of entries matching filters")
    limit: int = Field(..., description="Page size limit")
    offset: int = Field(..., description="Number of items skipped")
