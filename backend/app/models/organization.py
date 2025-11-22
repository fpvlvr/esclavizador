"""
Organization model.

Schema reference: implementation-plan.md lines 227-232
"""

from tortoise import fields
from tortoise.models import Model


class Organization(Model):

    id = fields.UUIDField(primary_key=True)
    name = fields.CharField(
        max_length=255,
        null=False,
        unique=True,
        description="Organization name (must be unique)"
    )
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "organizations"

    def __str__(self) -> str:
        return f"Organization(id={self.id}, name={self.name})"
