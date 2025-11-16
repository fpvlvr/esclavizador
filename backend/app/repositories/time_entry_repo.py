"""
Time entry repository for database operations.

Handles all database queries for TimeEntry model with multi-tenant isolation.
Returns TypedDict entities for ORM independence.
"""

from typing import Optional
from uuid import UUID
from datetime import datetime
from tortoise.queryset import Q

from app.models.time_entry import TimeEntry
from app.repositories.base import BaseRepository
from app.domain.entities import TimeEntryData


class TimeEntryRepository(BaseRepository[TimeEntry, TimeEntryData]):
    """Repository for time entry data access."""

    model = TimeEntry

    async def _to_dict(self, entry: TimeEntry) -> TimeEntryData:
        """
        Convert TimeEntry ORM instance to TimeEntryData dict.

        Requires prefetched relations: user, project, task (optional).
        """
        # Ensure relations are loaded
        await entry.fetch_related('user', 'project', 'task')

        # Compute duration if entry is stopped
        duration_seconds = None
        if entry.end_time:
            duration_seconds = int((entry.end_time - entry.start_time).total_seconds())

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
        description: Optional[str]
    ) -> TimeEntryData:
        """
        Create new time entry.

        Args:
            user_id: User UUID
            project_id: Project UUID
            task_id: Task UUID (optional)
            organization_id: Organization UUID
            start_time: Entry start time
            end_time: Entry end time (None for running timers)
            is_running: Whether timer is currently running
            is_billable: Whether time is billable
            description: Entry description (optional)

        Returns:
            TimeEntryData dict with prefetched relations
        """
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

        # Prefetch relations for conversion
        await entry.fetch_related('user', 'project', 'task')

        return await self._to_dict(entry)

    async def get_by_id(
        self,
        entry_id: str,
        org_id: str
    ) -> Optional[TimeEntryData]:
        """
        Get time entry by ID with multi-tenant filtering.

        Args:
            entry_id: TimeEntry UUID
            org_id: Organization UUID

        Returns:
            TimeEntryData dict with prefetched relations, or None if not found
        """
        entry = await self.model.filter(
            id=entry_id,
            organization_id=org_id
        ).prefetch_related('user', 'project', 'task').first()

        if not entry:
            return None

        return await self._to_dict(entry)

    async def get_running_entry(
        self,
        user_id: UUID | str,
        org_id: UUID | str
    ) -> Optional[TimeEntryData]:
        """
        Get currently running time entry for user.

        Args:
            user_id: User UUID
            org_id: Organization UUID

        Returns:
            TimeEntryData dict if running entry exists, else None
        """
        entry = await self.model.filter(
            user_id=user_id,
            organization_id=org_id,
            is_running=True
        ).prefetch_related('user', 'project', 'task').first()

        if not entry:
            return None

        return await self._to_dict(entry)

    async def stop_timer(
        self,
        entry_id: str,
        end_time: datetime
    ) -> TimeEntryData:
        """
        Stop a running timer.

        Args:
            entry_id: TimeEntry UUID
            end_time: Time when timer stopped

        Returns:
            Updated TimeEntryData dict

        Note: Caller should verify entry exists and is running
        """
        entry = await self.model.get(id=entry_id)
        entry.end_time = end_time
        entry.is_running = False
        await entry.save()

        await entry.fetch_related('user', 'project', 'task')
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
            start_time: Start of time range
            end_time: End of time range
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
        List time entries with filtering and pagination.

        Args:
            org_id: Organization UUID
            filters: Dict with optional keys:
                - user_id (str): Filter by user
                - project_id (str): Filter by project
                - task_id (str): Filter by task
                - is_billable (bool): Filter by billable status
                - is_running (bool): Filter by running status
                - start_date (date): Entries started on/after this date
                - end_date (date): Entries started on/before this date

            limit: Maximum items to return
            offset: Number of items to skip

        Returns:
            Dict with keys: items (list of TimeEntryData dicts), total (int)
        """
        # Base query with org filter
        query = self.model.filter(organization_id=org_id)

        # Apply optional filters
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

        # Date range filtering on start_time
        if 'start_date' in filters and filters['start_date']:
            # Convert date to datetime (start of day)
            start_dt = datetime.combine(filters['start_date'], datetime.min.time())
            query = query.filter(start_time__gte=start_dt)

        if 'end_date' in filters and filters['end_date']:
            # Convert date to datetime (end of day)
            end_dt = datetime.combine(filters['end_date'], datetime.max.time())
            query = query.filter(start_time__lte=end_dt)

        # Get total count
        total = await query.count()

        # Get paginated results with prefetched relations
        entries = await query.prefetch_related(
            'user', 'project', 'task'
        ).offset(offset).limit(limit).order_by('-start_time').all()

        # Convert to TimeEntryData dicts
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
        """
        Update time entry with multi-tenant filtering.

        Args:
            entry_id: TimeEntry UUID
            org_id: Organization UUID
            data: Dict of fields to update

        Returns:
            Updated TimeEntryData dict, or None if not found
        """
        # Get entry (verifies org ownership)
        entry = await self.model.filter(
            id=entry_id,
            organization_id=org_id
        ).first()

        if not entry:
            return None

        # Update fields
        for key, value in data.items():
            setattr(entry, key, value)

        await entry.save()

        # Fetch with relations for conversion
        await entry.fetch_related('user', 'project', 'task')
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


# Singleton instance
time_entry_repo = TimeEntryRepository()
