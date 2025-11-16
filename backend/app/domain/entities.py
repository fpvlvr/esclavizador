"""
Domain entity TypedDicts.

Defines the shape of data structures used throughout the application,
independent of ORM models or API schemas. These provide type safety
without coupling to specific implementations.

Usage:
    - Repositories return these TypedDicts
    - Services consume and return these TypedDicts
    - API layer converts these to Pydantic response models
"""

from typing import TypedDict, Optional
from uuid import UUID
from datetime import datetime


class UserData(TypedDict):

    id: UUID
    email: str
    password_hash: str  # Argon2id hashed password
    role: str  # "master" or "slave"
    organization_id: UUID
    is_active: bool
    created_at: datetime


class OrganizationData(TypedDict):

    id: UUID
    name: str
    created_at: datetime


class ProjectData(TypedDict):

    id: UUID
    name: str
    description: Optional[str]
    organization_id: UUID
    is_active: bool
    created_at: datetime
    task_count: int  # Computed via COUNT aggregation in repository


class TaskData(TypedDict):

    id: UUID
    name: str
    description: Optional[str]
    project_id: UUID
    project_name: str  # Extracted from prefetched project relation
    is_active: bool
    created_at: datetime


class RefreshTokenData(TypedDict):

    id: UUID
    user_id: UUID
    token_hash: str
    expires_at: datetime
    revoked_at: Optional[datetime]
    created_at: datetime


class TagData(TypedDict):

    id: UUID
    name: str
    organization_id: UUID
    created_at: datetime


class TimeEntryData(TypedDict):

    id: UUID
    user_id: UUID
    project_id: UUID
    task_id: Optional[UUID]
    organization_id: UUID
    start_time: datetime
    end_time: Optional[datetime]
    is_running: bool
    is_billable: bool
    description: Optional[str]
    created_at: datetime
    # Computed/extracted fields
    user_email: str  # Extracted from user.email
    project_name: str  # Extracted from project.name
    task_name: Optional[str]  # Extracted from task.name if task exists
    duration_seconds: Optional[int]  # Computed: (end_time - start_time).total_seconds()
    tags: list["TagData"]  # Extracted from prefetched tags relation
