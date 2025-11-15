"""
Tag model for categorizing time entries.

Schema reference: implementation-plan.md lines 301-313
"""

from tortoise import fields
from tortoise.models import Model


class Tag(Model):
    """
    Tag model for categorizing and labeling time entries.

    Tags are organization-scoped, with names unique within each organization.
    Multiple tags can be assigned to a single time entry via many-to-many relationship.
    """

    id = fields.UUIDField(primary_key=True)
    name = fields.CharField(max_length=100, null=False)
    organization: fields.ForeignKeyRelation["Organization"] = fields.ForeignKeyField(
        "models.Organization", related_name="tags", null=False, db_index=True
    )
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "tags"
        unique_together = [("name", "organization_id")]

    def __str__(self) -> str:
        return f"Tag(id={self.id}, name={self.name})"
