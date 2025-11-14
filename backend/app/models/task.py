"""
Task model.

Schema reference: implementation-plan.md lines 262-273
"""

from tortoise import fields
from tortoise.models import Model


class Task(Model):
    """
    Task model for granular work tracking within projects.

    Tasks belong to projects and are used to categorize time entries
    within a project's scope.
    """

    id = fields.UUIDField(pk=True)
    name = fields.CharField(max_length=255, null=False)
    description = fields.TextField(null=True)
    project: fields.ForeignKeyRelation["models.Project"] = fields.ForeignKeyField(
        "models.Project", related_name="tasks", null=False, index=True
    )
    is_active = fields.BooleanField(default=True, null=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "tasks"

    def __str__(self) -> str:
        return f"Task(id={self.id}, name={self.name})"
