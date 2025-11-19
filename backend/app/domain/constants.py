"""
Domain constants and enumerations.

Defines domain-level constants that are independent of ORM models or API schemas.
These can be used across all layers without creating unwanted dependencies.
"""

from enum import Enum


class UserRole(str, Enum):
    """User role enumeration - domain constant."""

    BOSS = "boss"  # Admin role with full access
    WORKER = "worker"  # Regular user with limited access

