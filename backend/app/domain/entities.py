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
