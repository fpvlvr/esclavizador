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
    """
    User entity data.

    Represents a user independent of ORM or API representation.
    """
    id: UUID
    email: str
    role: str  # "MASTER" or "SLAVE"
    organization_id: UUID
    is_active: bool
    created_at: datetime


class OrganizationData(TypedDict):
    """
    Organization entity data.

    Represents an organization independent of ORM or API representation.
    """
    id: UUID
    name: str
    is_active: bool
    created_at: datetime


class ProjectData(TypedDict):
    """
    Project entity data.

    Represents a project with computed task_count field.
    Returned by repository layer with all necessary data for API responses.
    """
    id: UUID
    name: str
    description: Optional[str]
    organization_id: UUID
    is_active: bool
    created_at: datetime
    task_count: int  # Computed via COUNT aggregation in repository


class TaskData(TypedDict):
    """
    Task entity data.

    Represents a task with project_name extracted from relation.
    Returned by repository layer with all necessary data for API responses.
    """
    id: UUID
    name: str
    description: Optional[str]
    project_id: UUID
    project_name: str  # Extracted from prefetched project relation
    is_active: bool
    created_at: datetime


class RefreshTokenData(TypedDict):
    """
    Refresh token entity data.

    Represents a refresh token record.
    """
    id: UUID
    user_id: UUID
    token_hash: str
    expires_at: datetime
    revoked: bool
    created_at: datetime
