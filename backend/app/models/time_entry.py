"""
Time entry model for tracking work time.

Schema reference: implementation-plan.md lines 275-300

Constraints:
- Only one running timer per user (partial unique index, added in migration)
- end_time >= start_time (check constraint, added in migration)
"""

from tortoise import fields
from tortoise.models import Model


class TimeEntry(Model):
    """
    Time entry model for tracking time spent on tasks.

    Supports two modes:
    1. Timer mode: Start with is_running=True, stop later (server-side tracking)
    2. Manual entry: Create with both start_time and end_time

    Constraints enforced via migration:
    - Only one running timer per user at a time
    - end_time must be >= start_time when not null
    """

    id = fields.UUIDField(primary_key=True)
    user: fields.ForeignKeyRelation["User"] = fields.ForeignKeyField(
        "models.User", related_name="time_entries", null=False, db_index=True
    )
    project: fields.ForeignKeyRelation["Project"] = fields.ForeignKeyField(
        "models.Project", related_name="time_entries", null=False, db_index=True
    )
    task: fields.ForeignKeyRelation["Task"] = fields.ForeignKeyField(
        "models.Task", related_name="time_entries", null=True, db_index=True
    )
    organization: fields.ForeignKeyRelation["Organization"] = fields.ForeignKeyField(
        "models.Organization", related_name="time_entries", null=False, db_index=True
    )
    start_time = fields.DatetimeField(null=False)
    end_time = fields.DatetimeField(null=True)
    is_running = fields.BooleanField(default=False, null=False, db_index=True)
    is_billable = fields.BooleanField(default=True, null=False)
    description = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    # Many-to-many relationship with tags
    tags: fields.ManyToManyRelation["Tag"] = fields.ManyToManyField(
        "models.Tag", related_name="time_entries", through="time_entry_tags"
    )

    class Meta:
        table = "time_entries"

    def __str__(self) -> str:
        return f"TimeEntry(id={self.id}, user_id={self.user_id}, is_running={self.is_running})"
