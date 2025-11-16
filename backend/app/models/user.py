"""
User model with authentication and role-based access control.

Schema reference: implementation-plan.md lines 234-247
"""

from enum import Enum
from tortoise import fields
from tortoise.models import Model


class UserRole(str, Enum):
    """User role enumeration."""

    BOSS = "boss"  # Admin role with full access
    WORKER = "worker"  # Regular user with limited access


class User(Model):
    """
    User model for authentication and authorization.

    Supports two roles:
    - boss: Admin with full CRUD access to organization data
    - worker: Regular user with limited access (own time entries only)
    """

    id = fields.UUIDField(primary_key=True)
    email = fields.CharField(max_length=255, unique=True, null=False, db_index=True)
    password_hash = fields.CharField(max_length=255, null=False)
    role = fields.CharEnumField(
        enum_type=UserRole, max_length=10, null=False, description="User role (boss/worker)"
    )
    organization: fields.ForeignKeyRelation["Organization"] = fields.ForeignKeyField(
        "models.Organization", related_name="users", null=False, db_index=True
    )
    is_active = fields.BooleanField(default=True, null=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "users"

    def __str__(self) -> str:
        return f"User(id={self.id}, email={self.email}, role={self.role})"
