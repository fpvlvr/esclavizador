"""
Organization model.

Schema reference: implementation-plan.md lines 227-232
"""

from tortoise import fields
from tortoise.models import Model


class Organization(Model):
    """
    Organization model for multi-tenant architecture.

    Each organization represents a separate company/entity using the system.
    All other entities (users, projects, tasks, etc.) belong to an organization.
    """

    id = fields.UUIDField(pk=True)
    name = fields.CharField(max_length=255, null=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "organizations"

    def __str__(self) -> str:
        return f"Organization(id={self.id}, name={self.name})"
