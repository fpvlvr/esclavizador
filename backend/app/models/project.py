"""
Project model.

Schema reference: implementation-plan.md lines 249-260
"""

from tortoise import fields
from tortoise.models import Model


class Project(Model):
    """
    Project model for organizing tasks and time entries.

    Projects belong to an organization and contain tasks.
    Time entries are tracked against specific projects.
    """

    id = fields.UUIDField(primary_key=True)
    name = fields.CharField(max_length=255, null=False)
    description = fields.TextField(null=True)
    organization: fields.ForeignKeyRelation["Organization"] = fields.ForeignKeyField(
        "models.Organization", related_name="projects", null=False, db_index=True
    )
    is_active = fields.BooleanField(default=True, null=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "projects"

    def __str__(self) -> str:
        return f"Project(id={self.id}, name={self.name})"
