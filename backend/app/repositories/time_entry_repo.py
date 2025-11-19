"""
Time entry repository for database operations.

Handles all database queries for TimeEntry model with multi-tenant isolation.
Returns TypedDict entities for ORM independence.
"""

from typing import Optional
from uuid import UUID
from datetime import datetime, date
from tortoise.queryset import Q

from app.models.time_entry import TimeEntry
from app.models.tag import Tag
from app.repositories.base import BaseRepository
from app.domain.entities import TimeEntryData, TagData, ProjectAggregateData


class TimeEntryRepository(BaseRepository[TimeEntry, TimeEntryData]):
    """Repository for time entry data access."""

    model = TimeEntry

    async def _validate_tags(self, tag_ids: list[str], org_id: str) -> list[Tag]:
        """Raises ValueError if any tag doesn't exist in organization."""
        if not tag_ids:
            return []

        tags = await Tag.filter(
            id__in=tag_ids,
            organization_id=org_id
        ).all()

        if len(tags) != len(tag_ids):
            found_ids = {str(tag.id) for tag in tags}
            missing_ids = [tid for tid in tag_ids if tid not in found_ids]
            raise ValueError(f"Tags not found in organization: {missing_ids}")

        return tags

    async def _to_dict(self, entry: TimeEntry) -> TimeEntryData:
        """
        Convert TimeEntry ORM instance to TimeEntryData dict.

        Requires prefetched relations: user, project, task (optional), tags.
        """
        # Ensure relations are loaded
        await entry.fetch_related('user', 'project', 'task', 'tags')

        # Compute duration if entry is stopped
        duration_seconds = None
        if entry.end_time:
            # Ensure both datetimes are timezone-aware for subtraction
            end_time = entry.end_time
            start_time = entry.start_time
            if end_time.tzinfo is None:
                from datetime import timezone
                end_time = end_time.replace(tzinfo=timezone.utc)
            if start_time.tzinfo is None:
                from datetime import timezone
                start_time = start_time.replace(tzinfo=timezone.utc)
            duration_seconds = int((end_time - start_time).total_seconds())

        # Convert tags to TagData dicts
        tags: list[TagData] = [
            {
                "id": tag.id,
                "name": tag.name,
                "organization_id": tag.organization_id,
                "created_at": tag.created_at,
            }
            for tag in entry.tags
        ]

        return {
            "id": entry.id,
            "user_id": entry.user_id,
            "project_id": entry.project_id,
            "task_id": entry.task_id,
            "organization_id": entry.organization_id,
            "start_time": entry.start_time,
            "end_time": entry.end_time,
            "is_running": entry.is_running,
            "is_billable": entry.is_billable,
            "description": entry.description,
            "created_at": entry.created_at,
            # Computed/extracted fields
            "user_email": entry.user.email,
            "project_name": entry.project.name,
            "task_name": entry.task.name if entry.task else None,
            "duration_seconds": duration_seconds,
            "tags": tags,
        }

    async def create(
        self,
        user_id: str,
        project_id: str,
        task_id: Optional[str],
        organization_id: str,
        start_time: datetime,
        end_time: Optional[datetime],
        is_running: bool,
        is_billable: bool,
        description: Optional[str],
        tag_ids: Optional[list[str]] = None
    ) -> TimeEntryData:
        entry = await self.model.create(
            user_id=user_id,
            project_id=project_id,
            task_id=task_id,
            organization_id=organization_id,
            start_time=start_time,
            end_time=end_time,
            is_running=is_running,
            is_billable=is_billable,
            description=description
        )

        # Add tags if provided
        if tag_ids:
            tag_objects = await self._validate_tags(tag_ids, organization_id)
            await entry.tags.add(*tag_objects)

        await entry.fetch_related('user', 'project', 'task', 'tags')
        return await self._to_dict(entry)

    async def get_by_id(
        self,
        entry_id: str,
        org_id: str
    ) -> Optional[TimeEntryData]:
        entry = await self.model.filter(
            id=entry_id,
            organization_id=org_id
        ).prefetch_related('user', 'project', 'task', 'tags').first()

        if not entry:
            return None

        return await self._to_dict(entry)

    async def get_running_entry(
        self,
        user_id: UUID | str,
        org_id: UUID | str
    ) -> Optional[TimeEntryData]:
        entry = await self.model.filter(
            user_id=user_id,
            organization_id=org_id,
            is_running=True
        ).prefetch_related('user', 'project', 'task', 'tags').first()

        if not entry:
            return None

        return await self._to_dict(entry)

    async def stop_timer(
        self,
        entry_id: str,
        end_time: datetime
    ) -> TimeEntryData:
        """Caller should verify entry exists and is running."""
        entry = await self.model.get(id=entry_id)
        entry.end_time = end_time
        entry.is_running = False
        await entry.save()

        await entry.fetch_related('user', 'project', 'task', 'tags')
        return await self._to_dict(entry)

    async def check_overlap(
        self,
        user_id: str,
        start_time: datetime,
        end_time: datetime,
        exclude_entry_id: Optional[str] = None
    ) -> bool:
        """
        Check if time range overlaps with existing entries for user.

        Args:
            user_id: User UUID
            start_time: Start of time range (timezone-aware UTC)
            end_time: End of time range (timezone-aware UTC)
            exclude_entry_id: Entry ID to exclude from check (for updates)

        Returns:
            True if overlap exists, False otherwise
        """
        query = self.model.filter(user_id=user_id)

        if exclude_entry_id:
            query = query.exclude(id=exclude_entry_id)

        # Check for overlap:
        # 1. Running timer started before our end_time
        # 2. Completed entry that overlaps our range
        # Overlap logic: NOT (new_end <= existing_start OR new_start >= existing_end)
        # Simplified: new_start < existing_end AND new_end > existing_start
        overlaps = await query.filter(
            Q(is_running=True, start_time__lt=end_time) |
            Q(is_running=False, start_time__lt=end_time, end_time__gt=start_time)
        ).exists()

        return overlaps

    async def list(
        self,
        org_id: UUID | str,
        filters: dict,
        limit: int,
        offset: int
    ) -> dict:
        """
        Filters: user_id, project_id, task_id, is_billable, is_running,
        start_date, end_date, tag_ids (list[str], OR logic).
        """
        query = self.model.filter(organization_id=org_id)

        if 'user_id' in filters and filters['user_id']:
            query = query.filter(user_id=filters['user_id'])

        if 'project_id' in filters and filters['project_id']:
            query = query.filter(project_id=filters['project_id'])

        if 'task_id' in filters and filters['task_id']:
            query = query.filter(task_id=filters['task_id'])

        if 'is_billable' in filters and filters['is_billable'] is not None:
            query = query.filter(is_billable=filters['is_billable'])

        if 'is_running' in filters and filters['is_running'] is not None:
            query = query.filter(is_running=filters['is_running'])

        if 'start_date' in filters and filters['start_date']:
            start_dt = datetime.combine(filters['start_date'], datetime.min.time())
            query = query.filter(start_time__gte=start_dt)

        if 'end_date' in filters and filters['end_date']:
            end_dt = datetime.combine(filters['end_date'], datetime.max.time())
            query = query.filter(start_time__lte=end_dt)

        # Tag filtering (OR logic - show entries with ANY of the specified tags)
        if 'tag_ids' in filters and filters['tag_ids']:
            query = query.filter(tags__id__in=filters['tag_ids'])

        total = await query.count()

        entries = await query.prefetch_related(
            'user', 'project', 'task', 'tags'
        ).offset(offset).limit(limit).order_by('-start_time').all()

        items = [await self._to_dict(entry) for entry in entries]

        return {
            "items": items,
            "total": total
        }

    async def update(
        self,
        entry_id: str,
        org_id: UUID | str,
        data: dict
    ) -> Optional[TimeEntryData]:
        """If 'tag_ids' in data, replaces all tags. If not provided, leaves tags unchanged."""
        entry = await self.model.filter(
            id=entry_id,
            organization_id=org_id
        ).first()

        if not entry:
            return None

        # Handle tag updates separately
        tag_ids = data.pop('tag_ids', None)

        # Update other fields
        for key, value in data.items():
            setattr(entry, key, value)

        await entry.save()

        # Update tags if provided (replaces all existing tags)
        if tag_ids is not None:
            await entry.fetch_related('tags')
            await entry.tags.clear()
            if tag_ids:  # Only add if list is not empty
                tag_objects = await self._validate_tags(tag_ids, str(org_id))
                await entry.tags.add(*tag_objects)

        await entry.fetch_related('user', 'project', 'task', 'tags')
        return await self._to_dict(entry)

    async def delete(
        self,
        entry_id: str,
        org_id: UUID | str
    ) -> bool:
        """
        Hard delete time entry (permanent removal).

        Args:
            entry_id: TimeEntry UUID
            org_id: Organization UUID

        Returns:
            True if deleted, False if not found
        """
        entry = await self.model.filter(
            id=entry_id,
            organization_id=org_id
        ).first()

        if not entry:
            return False

        await entry.delete()
        return True

    async def aggregate_by_project(
        self,
        org_id: UUID | str,
        user_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> list[ProjectAggregateData]:
        """
        Aggregate time entries by project.

        Groups completed time entries by project and calculates:
        - total_seconds: Sum of all duration_seconds for the project
        - billable_seconds: Sum of duration_seconds where is_billable=True

        Args:
            org_id: Organization UUID
            user_id: Optional user ID filter (for workers seeing only their entries)
            start_date: Optional start date filter (entries >= this date)
            end_date: Optional end date filter (entries <= this date)

        Returns:
            List of ProjectAggregateData dicts
        """
        # Build base query - only completed entries
        query = self.model.filter(
            organization_id=org_id,
            is_running=False
        )

        # Apply filters
        if user_id:
            query = query.filter(user_id=user_id)

        if start_date:
            start_dt = datetime.combine(start_date, datetime.min.time())
            query = query.filter(start_time__gte=start_dt)

        if end_date:
            end_dt = datetime.combine(end_date, datetime.max.time())
            query = query.filter(start_time__lte=end_dt)

        # Fetch entries with project relation
        entries = await query.prefetch_related('project').all()

        # Aggregate by project
        project_aggregates: dict[str, ProjectAggregateData] = {}

        for entry in entries:
            # Skip entries without end_time (shouldn't happen for is_running=False, but safety check)
            if not entry.end_time or not entry.start_time:
                continue

            # Calculate duration
            end_time = entry.end_time
            start_time = entry.start_time
            # Ensure timezone-aware
            if end_time.tzinfo is None:
                from datetime import timezone
                end_time = end_time.replace(tzinfo=timezone.utc)
            if start_time.tzinfo is None:
                from datetime import timezone
                start_time = start_time.replace(tzinfo=timezone.utc)

            duration_seconds = int((end_time - start_time).total_seconds())

            # Get project info (already prefetched)
            project_id = entry.project_id  # Keep as UUID
            project_name = entry.project.name
            project_id_str = str(project_id)

            # Initialize project aggregate if not exists
            if project_id_str not in project_aggregates:
                project_aggregates[project_id_str] = {
                    'project_id': project_id,
                    'project_name': project_name,
                    'total_seconds': 0,
                    'billable_seconds': 0,
                }

            # Add to totals
            project_aggregates[project_id_str]['total_seconds'] += duration_seconds
            if entry.is_billable:
                project_aggregates[project_id_str]['billable_seconds'] += duration_seconds

        # Convert to list and sort by total_seconds descending
        return sorted(
            list(project_aggregates.values()),
            key=lambda x: x['total_seconds'],
            reverse=True
        )


# Singleton instance
time_entry_repo = TimeEntryRepository()
